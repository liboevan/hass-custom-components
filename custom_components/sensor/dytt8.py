'''
# Module name:
    dytt8.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests and bs4

# Purpose:
    New movies/tv plays sensor powered by Dytt8

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Oct.1st 2017

# Last Modified:
    Oct.13th 2017
'''

from datetime import datetime, timedelta
import logging
import re

from bs4 import BeautifulSoup
import requests
import voluptuous as vol

from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE, CONF_API_KEY, CONF_MONITORED_CONDITIONS, CONF_NAME, TEMP_CELSIUS, ATTR_ATTRIBUTION)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Dytt8'
ATTRIBUTION = 'Powered by Dytt8'

#PAT_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
PAT_MOVIE_NAME = re.compile(r'.+《(.+)》.+')
DECOLLATOR = ' | '

CONF_UPDATE_INTERVAL = 'update_interval'
CONF_MONITORED_CONDITIONS = 'monitored_conditions'

SENSOR_MOVIE = 'movie'
SENSOR_EN_TV_PLAY = 'en_tv_play'

SENSOR_TYPES = {
    SENSOR_MOVIE: ['Movie', 'mdi:movie'],
    SENSOR_EN_TV_PLAY: ['TV play', 'mdi:movie'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(minutes=15)): (vol.All(cv.time_period, cv.positive_timedelta)),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    interval = config.get(CONF_UPDATE_INTERVAL)
    monitored_conditions = config.get(CONF_MONITORED_CONDITIONS)  
    dytt8_data = Dytt8Data(interval)
    dytt8_data.update()
    # If connection failed don't setup platform.
    if dytt8_data.data is None:
        _LOGGER.error('movie_data.data is None, will not generate sensor.')
        return False

    sensors = []
    for variable in monitored_conditions:
        sensors.append(Dytt8Sensor(hass, dytt8_data, variable))
    add_devices(sensors, True)


class Dytt8Sensor(Entity):
    def __init__(self, hass, dytt8_data, sensor_type):
        """Initialize the sensor."""
        self.dytt8_data = dytt8_data
        self.type = sensor_type
        self.entity_id = generate_entity_id('sensor.{}', self.type, hass=hass)
        self.display_name = SENSOR_TYPES[self.type][0]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.display_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][1]

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        data = self.dytt8_data.data[self.type]
        if data is not None:
            attrs = data[1]
        else:
            attrs = {}
        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrs

    def update(self):
        self.dytt8_data.update()
        data = self.dytt8_data.data[self.type]
        if data is not None:
            self._state = data[0]


class Dytt8Data(object):
    def __init__(self, internal):
        self.data = None
        self._home_url = 'http://www.dytt8.net'
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    def _update(self):
        rep = requests.get(self._home_url)
        rep.encoding = 'gb2312'
        soup = BeautifulSoup(rep.text, 'html.parser')
        # The first div of co_content8 is new movies
        new_movies_soup = soup.find('div', class_='co_content8')
        # The second div of co_content3 is en tv plays
        tv_list = soup.find_all('div', class_='co_content3')
        en_tv_plays_soup = None
        if tv_list is not None:
            tv_count = len(tv_list)
            if tv_count > 1:
                en_tv_plays_soup = tv_list[1]
        new_movies_data = self._get_data(new_movies_soup)
        en_tv_plays_data = self._get_data(en_tv_plays_soup)
        if new_movies_data is None and en_tv_plays_data is None:
            _LOGGER.error('Both new_movies_data and en_tv_plays_data are none.')
            return
        data = {}
        data[SENSOR_MOVIE] = new_movies_data
        data[SENSOR_EN_TV_PLAY] = en_tv_plays_data
        self.data = data

    def _get_data(self, resource_soup):
        if resource_soup is None:
            _LOGGER.error('resource_soup is None.')
            return None
        resources = resource_soup.find_all('tr')
        tr_count = len(resources)
        if tr_count <= 0:
            _LOGGER.error('No any trs in resource_soup.')
            return None
        first = resources[0]
        last_date = first.find('font')
        if last_date is None:
            _LOGGER.error('No font in resource tr.')
            return None
        last_date = last_date.text
        state = ''
        attributes = {}
        for resource in resources:
            if resource.find('font').text == last_date:
                resource = resource.find('td').find_all('a')[1]
                r_name = re.findall(PAT_MOVIE_NAME, resource.text)[0]
                r_url = self._home_url + resource['href']
                state = state + r_name + DECOLLATOR
                attributes[r_name] = r_url
        state = state.strip(DECOLLATOR)
        return state, attributes
