'''
# Module name:
    heweather.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests

# Purpose:
    weather sensor powered by He Weather

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Aug.24th 2017

'''

import logging
from datetime import timedelta
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import requests
import voluptuous as vol

from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE, CONF_API_KEY, CONF_MONITORED_CONDITIONS, CONF_NAME, TEMP_CELSIUS, ATTR_ATTRIBUTION)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'He Weather'
ATTRIBUTION = 'Powered by He Weather'

CONF_UPDATE_INTERVAL = 'update_interval'
CONF_CITY = 'city'
CONF_LANG = 'lang'
CONF_FORECAST = 'forecast'

SENSOR_TYPES = {
    # AQI
    'aqi': ['AQI', 'AQI', 'mdi:cloud'],
    # Now
    'summary': ['Now', None, None],
    # Daily
    'daily_astro_sr': ['Sun Raise', None, 'mdi:weather-sunset-up'],
    'daily_astro_ss': ['Sun Set', None, 'mdi:weather-sunset-down'],
    'daily_summary_day': ['Summary Day', None, None],
    'daily_summary_night': ['Summary Night', None, None],
    'daily_hum': ['Humidity', '%', 'mdi:water-percent'],
    'daily_pcpn': ['Precip Intensity', 'mm', 'mdi:weather-rainy'],
    'daily_pop': ['Precip Posibility', '%', 'mdi:weather-rainy'],
    'daily_pres': ['Pressure', 'hPa', 'mdi:gauge'],
    'daily_tmp_max': ['Max Temperature', '°C', 'mdi:thermometer'],
    'daily_tmp_min': ['Min Temperature', '°C', 'mdi:thermometer'],
    'daily_vis': ['Visibility', 'Km', 'mdi:eye'],
    'daily_wind_deg': ['Wind Bearing', '°', 'mdi:compass'],
    'daily_wind_dir': ['Wind Direction', None, 'mdi:compass'],
    'daily_wind_sc': ['Wind Scale', None, 'mdi:weather-windy'],
    'daily_wind_spd': ['Wind Speed', 'Km/h', 'mdi:weather-windy'],
}

AQI_ATTR_TYPES = {
    'pm10': 'pm 10 (mg/m3)',
    'pm25': 'pm 2.5 (μg/m3)',
    'qlty': 'quality'
}

NOW_ATTR_TYPES = {
    'fl': 'feeling (°C)',
    'hum': 'humidity (%)',
    'pcpn': 'precip intensity (mm)',
    'pres': 'pressure (hPa)',
    'tmp': 'temperature (°C)',
    'vis': 'visibility (Km)',
    'dir': 'wind direction',
    'sc': 'wind scale',
}

CONDITION_PICTURES = {
    '100':'http://www.z4a.net/images/2017/03/29/100.png',
    '101':'http://www.z4a.net/images/2017/03/29/101.png',
    '102':'http://www.z4a.net/images/2017/03/29/102.png',
    '103':'http://www.z4a.net/images/2017/03/29/103.png',
    '104':'http://www.z4a.net/images/2017/03/29/104.png',

    '200':'http://www.z4a.net/images/2017/03/29/200.png',
    '201':'http://www.z4a.net/images/2017/03/29/201.png',
    '202':'http://www.z4a.net/images/2017/03/29/202.png',
    '203':'http://www.z4a.net/images/2017/03/29/202.png',
    '204':'http://www.z4a.net/images/2017/03/29/202.png',
    '205':'http://www.z4a.net/images/2017/03/29/205.png',
    '206':'http://www.z4a.net/images/2017/03/29/205.png',
    '207':'http://www.z4a.net/images/2017/03/29/205.png',
    '208':'http://www.z4a.net/images/2017/03/29/208.png',
    '209':'http://www.z4a.net/images/2017/03/29/208.png',
    '210':'http://www.z4a.net/images/2017/03/29/208.png',
    '211':'http://www.z4a.net/images/2017/03/29/208.png',
    '212':'http://www.z4a.net/images/2017/03/29/208.png',
    '213':'http://www.z4a.net/images/2017/03/29/208.png',

    '300':'http://www.z4a.net/images/2017/03/29/300.png',
    '301':'http://www.z4a.net/images/2017/03/29/301.png',
    '302':'http://www.z4a.net/images/2017/03/29/302.png',
    '303':'http://www.z4a.net/images/2017/03/29/303.png',
    '304':'http://www.z4a.net/images/2017/03/29/304.png',
    '305':'http://www.z4a.net/images/2017/03/29/305.png',
    '306':'http://www.z4a.net/images/2017/03/29/306.png',
    '307':'http://www.z4a.net/images/2017/03/29/307.png',
    '308':'http://www.z4a.net/images/2017/03/29/308.png',
    '309':'http://www.z4a.net/images/2017/03/29/309.png',
    '310':'http://www.z4a.net/images/2017/03/29/310.png',
    '311':'http://www.z4a.net/images/2017/03/29/311.png',
    '312':'http://www.z4a.net/images/2017/03/29/311.png',
    '313':'http://www.z4a.net/images/2017/03/29/313.png',

    '400':'http://www.z4a.net/images/2017/03/29/400.png',
    '401':'http://www.z4a.net/images/2017/03/29/401.png',
    '402':'http://www.z4a.net/images/2017/03/29/402.png',
    '403':'http://www.z4a.net/images/2017/03/29/403.png',
    '404':'http://www.z4a.net/images/2017/03/29/404.png',
    '405':'http://www.z4a.net/images/2017/03/29/405.png',
    '406':'http://www.z4a.net/images/2017/03/29/406.png',
    '407':'http://www.z4a.net/images/2017/03/29/407.png',

    '500':'http://www.z4a.net/images/2017/03/29/500.png',
    '501':'http://www.z4a.net/images/2017/03/29/501.png',
    '502':'http://www.z4a.net/images/2017/03/29/502.png',
    '503':'http://www.z4a.net/images/2017/03/29/503.png',
    '504':'http://www.z4a.net/images/2017/03/29/504.png',
    '505':'http://www.z4a.net/images/2017/03/29/504.png',
    '506':'http://www.z4a.net/images/2017/03/29/504.png',
    '507':'http://www.z4a.net/images/2017/03/29/507.png',
    '508':'http://www.z4a.net/images/2017/03/29/508.png',

    '900':'http://www.z4a.net/images/2017/03/29/900.png',
    '901':'http://www.z4a.net/images/2017/03/29/901.png',
    '999':'http://www.z4a.net/images/2017/03/29/999.png',
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Required(CONF_API_KEY): cv.string,
    vol.Inclusive(CONF_LATITUDE, 'coordinates', 'Latitude and longitude must exist together'): cv.latitude,
    vol.Inclusive(CONF_LONGITUDE, 'coordinates', 'Latitude and longitude must exist together'): cv.longitude,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_CITY, default=None): cv.string,
    vol.Optional(CONF_LANG): cv.string,
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(seconds=120)): (vol.All(cv.time_period, cv.positive_timedelta)),
    vol.Optional(CONF_FORECAST): vol.All(cv.ensure_list, [vol.Range(min=1, max=2)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the He Weather sensor."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    api_key = config.get(CONF_API_KEY, None)
    interval = config.get(CONF_UPDATE_INTERVAL)
    city = config.get(CONF_CITY)
    forecast = config.get(CONF_FORECAST)
    lang = config.get(CONF_LANG)
    monitored_conditions = config[CONF_MONITORED_CONDITIONS]

    forecast_days = (1 if forecast is None else max(forecast) + 1)
    has_aqi = 'aqi' in monitored_conditions
    has_now = 'summary' in monitored_conditions
    has_daily = False
    for variable in monitored_conditions:
        if 'daily' in variable:
            has_daily = True
            break
    forecast_days = (forecast_days if has_daily else 0)

    forecast_data = HeWeatherData(api_key, latitude, longitude, city, interval, has_aqi, has_now, forecast_days, lang)
    forecast_data.update()
    # If connection failed don't setup platform.
    if forecast_data.data is None:
        return False

    name = config[CONF_NAME]
    sensors = []
    for variable in monitored_conditions:
        sensors.append(HeWeatherSensor(forecast_data, variable, name))
        if forecast is not None and variable.startswith('daily'):
            for forecast_day in forecast:
                sensors.append(HeWeatherSensor(forecast_data, variable, name, forecast_day))

    add_devices(sensors, True)

class HeWeatherSensor(Entity):
    def __init__(self, forecast_data, sensor_type, name, forecast_day=0):
        """Initialize the sensor."""
        self.forecast_data = forecast_data
        self.client_name = name
        self.type = sensor_type
        self.forecast_day = forecast_day
        self._name = SENSOR_TYPES[sensor_type][0]
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._state = None
        self._icon = None  

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.forecast_day == 0:
            return '{0} {1}'.format(self.client_name, self._name)
        if self.forecast_day == 1:
            return '{0} {1} {2}'.format(self.client_name, self._name, 'Tomorrow')
        if self.forecast_day == 2:
            return '{0} {1} {2}'.format(self.client_name, self._name, 'After Tomorrow')

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def entity_picture(self):
        """Return the entity picture to use in the frontend, if any."""
        if self._icon is None or 'summary' not in self.type:
            return None
        if self._icon in CONDITION_PICTURES:
            return CONDITION_PICTURES[self._icon]
        return None

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][2]

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        attrs[ATTR_ATTRIBUTION] = '{0} {1}'.format(self.forecast_data.data['last_update'], ATTRIBUTION)
        
        if self.type == 'aqi':
            aqi_data = self.forecast_data.data['aqi']
            if aqi_data is not None:
                for key, value in AQI_ATTR_TYPES.items():
                    data = aqi_data[key]
                    attrs[value] = data
        elif self.type == 'summary':
            now_data = self.forecast_data.data['now']
            if now_data is not None:
                for key, value in NOW_ATTR_TYPES.items():
                    if key in ('dir', 'sc'):
                        data = now_data['wind'][key]
                    else:
                        data = now_data[key]
                    attrs[value] = data        
        
        return attrs

    def update(self):
        """Get the latest data from He Weather and updates the states."""
        self.forecast_data.update()

        if self.type == 'aqi':
            aqi_data = self.forecast_data.data['aqi']
            if aqi_data is None:
                return
            self._state = aqi_data[self.type]
        elif self.type == 'summary':
            now_data = self.forecast_data.data['now']
            if now_data is None:
                return
            summary_data = now_data['cond']
            self._state = summary_data['txt'].title()
            self._icon = summary_data['code']
        else:
            daily_data = self.forecast_data.data['daily']
            if daily_data is None:
                return
            day_data = daily_data[self.forecast_day]
            if self.type in ('daily_hum', 'daily_pcpn', 'daily_pop', 'daily_pres', 'daily_vis'):
                pure_type = self.type.replace('daily_', '')
                self._state = day_data[pure_type]
            elif 'daily_wind' in self.type:
                wind_data = day_data['wind']
                pure_type = self.type.replace('daily_wind_', '')
                self._state = wind_data[pure_type]
            elif 'daily_astro' in self.type:
                astro_data = day_data['astro']
                pure_type = self.type.replace('daily_astro_', '')
                self._state = astro_data[pure_type]
            elif 'daily_tmp' in self.type:
                tmp_data = day_data['tmp']
                pure_type = self.type.replace('daily_tmp_', '')
                self._state = tmp_data[pure_type]
            elif 'daily_summary' in self.type:
                summary_data = daily_data[self.forecast_day]['cond']
                if self.type == 'daily_summary_day':
                    self._state = summary_data['txt_d'].title()
                    self._icon = summary_data['code_d']
                elif self.type == 'daily_summary_night':
                    self._state = summary_data['txt_n'].title()
                    self._icon = summary_data['code_n']

class HeWeatherData(object):
    """Get the latest data from Darksky."""

    def __init__(self, api_key, latitude, longitude, city, interval, is_forecast_aqi, is_forecast_now, forecast_days, lang):
        """Initialize the data object."""
        self._api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.city = city
        self.is_forecast_aqi = is_forecast_aqi
        self.is_forecast_now = is_forecast_now
        self.forecast_days = forecast_days
        self.lang = lang
        self.data = None
        # Apply throttling to methods using configured interval
        self.update = Throttle(interval)(self._update)

    def _update(self):
        """Get the latest data from He Weather."""
        if self.city is not None:
            city = self.city
        else:
            city = '{0},{1}'.format(self.longitude, self.latitude)

        url = 'https://free-api.heweather.com/v5/weather?key={0}&lang={1}&city={2}'.format(self._api_key, self.lang, city)
        resp = None
        try:
            resp = requests.get(url)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            _LOGGER.error("Unable to connect to Dark Sky. %s", error)
            return
        if resp.status_code != 200:
            _LOGGER.error('http error: %s', resp.status_code)
            return
        rst_json = resp.json()
        if not 'HeWeather5' in rst_json:
            _LOGGER.error('response error 1.')
            return
        wea_json = rst_json['HeWeather5'][0] 
        if wea_json['status'] != 'ok':
            _LOGGER.error('response error 2.')
            return

        self.data = {}
        self.data['last_update'] = wea_json['basic']['update']['loc']
        if self.is_forecast_aqi:
            self.data['aqi'] = wea_json['aqi']['city']
        if self.is_forecast_now:
            self.data['now'] = wea_json['now']
        daily = []
        for day in range(self.forecast_days):
            daily.append(wea_json['daily_forecast'][day])
        self.data['daily'] = daily
