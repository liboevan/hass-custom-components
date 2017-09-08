'''
# Module name:
    jdfundindex.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests and bs4

# Purpose:
    Fund index sensor powered by JD

# Author:
    Retroposter retroposter@outlook.com
    
# Created:
    Sep.8th 2017
'''

from datetime import datetime, timedelta
import json
import logging
import time

from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import requests
import re
import voluptuous as vol

from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE, CONF_API_KEY, CONF_MONITORED_CONDITIONS, CONF_NAME, TEMP_CELSIUS, ATTR_ATTRIBUTION)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = 'Fund Index'
ATTRIBUTION = 'Powered by JD'

CONF_UPDATE_INTERVAL = 'update_interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(hours=1)): (vol.All(cv.time_period, cv.positive_timedelta))
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Fund sensor."""
    name = config[CONF_NAME]
    interval = config.get(CONF_UPDATE_INTERVAL)
    index_data = JdFundIndexData(interval)
    index_data.update()
    # If connection failed don't setup platform.
    if index_data.data is None:
        return False
    sensors = [JdFundIndexSensor(index_data, name)]
    add_devices(sensors, True)


class JdFundIndexSensor(Entity):
    def __init__(self, index_data, name):
        """Initialize the sensor."""
        self.index_data = index_data
        self.client_name = name
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
        if self._state < 41:
            return 'mdi:emoticon-sad'
        if self._state < 50:
            return 'mdi:emoticon-neutral'
        if self._state < 61:
            return 'mdi:emoticon-happy'
        return 'mdi:emoticon-excited'

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return 'Pts'

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        data = self.index_data.data
        if data is None:
            attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
            return attrs
        attrs[ATTR_ATTRIBUTION] = '{0} {1}'.format(data['index_date'], ATTRIBUTION)
        attrs['整体走势'] = data['summary']
        if data['hot_list'] is not None:
            for hot in data['hot_list']:
                attrs[hot['name']] = hot['index']
        return attrs

    def update(self):
        """Get the latest data from He Weather and updates the states."""
        self.index_data.update()
        data = self.index_data.data
        if data is None:
            return
        self._state = data['index']


class JdFundIndexData(object):
    """Get the latest data from JD."""

    def __init__(self, internal):
        self.data = None
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    def _update(self):
        timespan = str(time.time())
        resp = None
        try:
            resp = requests.post('https://licai.jd.com//async/financing/getJZBroadCast.action?_dc=' + timespan)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            _LOGGER.error('Unable to connect to licai.jd.com. %s', error)
            return
        if resp is None:
            return
        json_data = json.loads(resp.text)
        self.data = {}     
        self.data['index'] = json_data['heat']
        self.data['index_date'] = json_data['degreeDateStr'][0:-3]
        self.data['summary'] = json_data['shareAdvise']

        resp = None
        try:
            resp = requests.post('https://fund.jd.com/topicRecommend.action?t=' + timespan)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            _LOGGER.error('Unable to connect to fund.jd.com. %s', error)
            return
        if resp is None:
            return
        json_data = json.loads(resp.text)
        hot_list = []
        for industry in json_data:
            hot = {'name': industry['strategyName'], 'index': industry['degree']}
            hot_list.append(hot)
        self.data['hot_list'] = hot_list
