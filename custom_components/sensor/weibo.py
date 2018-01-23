
'''
# Module name:
    weibo.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests

# Purpose:
    Weibo sensor powered by Sina Weibo

# Author:
    Retroposter retroposter@outlook.com
    Based on https://github.com/naiquann/WBMonitor/blob/master/weiboMonitor.py

# Created:
    Sep.22th 2017

# Last Modified:
    Jan.23th 2018
'''

import logging
from datetime import timedelta
import re
import requests
import voluptuous as vol

from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE, CONF_API_KEY, CONF_MONITORED_CONDITIONS, CONF_NAME, TEMP_CELSIUS, ATTR_ATTRIBUTION)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Weibo'
ATTRIBUTION = 'Powered by Sina Weibo'

PAT_EMOTION_PREFIX = re.compile(r'<span.*?alt="')
PAT_TAG_PREFIX = re.compile(r"<a class='k'.*?from=feed'>")
PAT_AT_PREFIX = re.compile(r'<a href.*?>')

CONF_UPDATE_INTERVAL = 'update_interval'
CONF_NAME = 'name'
CONF_ICON = 'icon'
CONF_TARGET_USER_ID = 'target_user_id'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_TARGET_USER_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ICON, default='mdi:emoticon'): cv.string,
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(minutes=5)): (vol.All(cv.time_period, cv.positive_timedelta)),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Weibo sensor.""" 
    target_user_id = config[CONF_TARGET_USER_ID]
    name = config[CONF_NAME]
    icon = config[CONF_ICON]
    interval = config.get(CONF_UPDATE_INTERVAL)
    weibo_data = WeiboData(target_user_id, interval)
    weibo_data.update()
    # If connection failed don't setup platform.
    if weibo_data.data is None:
        _LOGGER.error('weibo_data.data is None, will not generate sensor.')
        return False

    sensors = [WeiboSensor(weibo_data, name, icon)]
    add_devices(sensors, True)


class WeiboSensor(Entity):
    def __init__(self, weibo_data, name, icon):
        """Initialize the sensor."""
        self.weibo_data = weibo_data
        self.client_name = name
        self._icon = icon
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.client_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        data = self.weibo_data.data
        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        attrs['link'] = data['link']
        #attrs['created at'] = data['created_at']
        #attrs['source'] = data['source']
        return attrs

    def update(self):
        """Get the latest data and updates the states."""
        self.weibo_data.update()
        data = self.weibo_data.data
        self._state = data['text']


class WeiboData(object):
    """Get the latest data from Weibo."""

    def __init__(self, user_id, internal):
        self.user_id = user_id
        self._session = requests.session()
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://passport.weibo.cn/signin/login',
            'Connection': 'close',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        self.data = None
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    def _update(self):
        """Get the latest weibo from Weibo."""
        # Get user weibo containerid
        user_info = 'https://m.weibo.cn/api/container/getIndex?uid={0}&type=uid&value={1}'.format(self.user_id, self.user_id)
        try:
            rep = self._session.get(user_info, headers=self._headers)
            for tab in rep.json()['tabsInfo']['tabs']:
                if tab['tab_type'] == 'weibo':
                    container_id = tab['containerid']
        except Exception as ex:
            _LOGGER.error('Failed to get containerid')
            _LOGGER.exception(ex)
            return
        # Get user weibo index
        self._target_info = 'https://m.weibo.cn/api/container/getIndex?uid={0}&type=uid&value={1}&containerid={2}'.format(self.user_id, self.user_id, container_id)
        latest_card = None
        try:
            rep = self._session.get(self._target_info, headers=self._headers)
            for card in rep.json()['cards']:
                if card['card_type'] == 9:
                    latest_card = card
                    break
        except Exception as ex:
            _LOGGER.error('Failed to get latest weibo')
            _LOGGER.exception(ex)
            return
        if latest_card is None:
            _LOGGER.error('No any cards')
            return
        self.data = {}
        self.data['link'] = latest_card['scheme']
        mblog = latest_card['mblog']
        self.data['created_at'] = mblog['created_at']
        self.data['source'] = mblog['source']
        if 'raw_text' in mblog:
            raw_text = mblog['raw_text']
            self.data['text'] = raw_text
            return
        text = mblog['text']
        span_list = re.findall(PAT_EMOTION_PREFIX, text)
        for item in span_list:
            text = text.replace(item, '').replace('"></span>', '')
        a_list = re.findall(PAT_TAG_PREFIX, text)
        for item in a_list:
            text = text.replace(item, '').replace('</a>', '')
        a_list = re.findall(PAT_AT_PREFIX, text)
        for item in a_list:
            text = text.replace(item, '').replace('</a>', '')
        text = text.replace('<br/>', '')
        self.data['text'] = text
