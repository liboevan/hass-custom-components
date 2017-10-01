
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
    Oct.1th 2017

# Last Modified:
    Oct.1th 2017
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

PAT_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
PAT_MOVIE_NAME = re.compile(r'.+《(.+)》.+')

CONF_UPDATE_INTERVAL = 'update_interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(hours=1)): (vol.All(cv.time_period, cv.positive_timedelta)),
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
        attrs = {}
        data = self.movie_data.data
        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        for key in data:
            attrs[key] = data[key]
        return attrs

    def update(self):
        self.movie_data.update()
        data = self.movie_data.data
        state = ''
        for key in data.keys():
            state = state + key + ' | '
        self._state = state.strip(' | ')


class Dytt8Data(object):
    def __init__(self, internal):
        self.data = None
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    def _update(self):
        HOME_URL = 'http://www.dytt8.net'
        # Find latest movies
        new_movies_url = HOME_URL + '/html/gndy/dyzz/index.html'
        rep = requests.get(new_movies_url)
        rep.encoding = 'gb2312'
        soup = BeautifulSoup(rep.text, 'html.parser')
        content = soup.find('div', class_='co_content8')
        movie_list = content.find_all('table')
        movie_count = len(movie_list)
        if movie_count == 0:
            _LOGGER.error('No any movies in the page.')
            return
        first_movive = movie_list[0]
        last_day = re.findall(PAT_DATE, first_movive.find('font').text)[0]
        movie_dict = {}
        for movie in movie_list:
            date_str = re.findall(PAT_DATE, movie.find('font').text)[0]
            if date_str != last_day:
                break
            movie = movie.find('a')
            movie_url = HOME_URL + movie['href']
            movie_name = re.findall(PAT_MOVIE_NAME, movie.text)[0]
            movie_dict[movie_name] = movie_url
        # Find download urls
        for key in movie_dict:
            url = movie_dict[key]
            download_link = self._get_download_link(url)
            movie_dict[key] = download_link
        self.data = movie_dict

    def _get_download_link(self, movie_url):
        try:
            rep = requests.get(movie_url)
            rep.encoding = 'gb2312'
            soup = BeautifulSoup(rep.text, 'html.parser')
            movie_zone = soup.find('div', id='Zoom')
            download_link = movie_zone.find('a')['href']
            return download_link
        except:
            _LOGGER.error('Failed to get download url in %s', movie_url)
            return None
