
'''
# Module name:
    dytt8.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests and bs4

# Purpose:
    New movies sensor powered by Dytt8

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Oct.1st 2017

# Last Modified:
    Oct.10TH 2017
'''

from datetime import datetime, timedelta
import logging
import re

from bs4 import BeautifulSoup
import requests
import voluptuous as vol

from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE, CONF_API_KEY, CONF_MONITORED_CONDITIONS, CONF_NAME, TEMP_CELSIUS, ATTR_ATTRIBUTION)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Dytt8'
ATTRIBUTION = 'Powered by Dytt8'

#PAT_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
PAT_MOVIE_NAME = re.compile(r'.+《(.+)》.+')
DECOLLATOR = ' | '

CONF_UPDATE_INTERVAL = 'update_interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(minutes=15)): (vol.All(cv.time_period, cv.positive_timedelta)),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    interval = config.get(CONF_UPDATE_INTERVAL)
    movie_data = Dytt8Data(interval)
    movie_data.update()
    # If connection failed don't setup platform.
    if movie_data.data is None:
        _LOGGER.error('movie_data.data is None, will not generate sensor.')
        return False

    sensors = [Dytt8Sensor(movie_data, DEFAULT_NAME)]
    add_devices(sensors, True)


class Dytt8Sensor(Entity):
    def __init__(self, movie_data, name):
        """Initialize the sensor."""
        self.movie_data = movie_data
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
        return 'mdi:movie'

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = self.movie_data.data[1]
        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrs

    def update(self):
        self.movie_data.update()
        self._state = self.movie_data.data[0]


class Dytt8Data(object):
    def __init__(self, internal):
        self.data = None
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    def _update(self):
        home_url = 'http://www.dytt8.net'
        rep = requests.get(home_url)
        rep.encoding = 'gb2312'
        soup = BeautifulSoup(rep.text, 'html.parser')
        content = soup.find('div', class_='co_content8')
        if content is None:
            _LOGGER.error('No div of co_content8 in the page.')
            return
        new_movie_table = content.find('table')
        if new_movie_table is None:
            _LOGGER.error('No any tables in the page.')
            return
        new_movies = new_movie_table.find_all('tr')
        tr_count = len(new_movies)
        if tr_count <= 0:
            _LOGGER.error('No any tds in the first table.')
            return
        first_movie = new_movies[0]
        last_date = first_movie.find('font')
        if last_date is None:
            _LOGGER.error('No font in the movie tr.')
            return
        last_date = last_date.text
        state = ''
        attributes = {}
        for new_movie in new_movies:
            if new_movie.find('font').text == last_date:
                movie = new_movie.find('td').find_all('a')[1]
                movie_name = re.findall(PAT_MOVIE_NAME, movie.text)[0]
                movie_url = home_url + movie['href']
                state = state + movie_name + DECOLLATOR
                attributes[movie_name] = movie_url
        state = state.strip(DECOLLATOR)
        self.data = state, attributes
