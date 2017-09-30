'''
# Module name:
    baidu.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests.

# Purpose:
    Baidu tts powered by Baidu.

# Author:
    Charleyzhu, Retroposter retroposter@outlook.com
    Retroposter copied from https://github.com/charleyzhu/HomeAssistant_Components/blob/master/tts/baidu.py
    Cannot stand charley's coding style, seriously.

# Created:
    Sep.4th 2017

# Last Modified:
    Sep.4th 2017
'''

import json
import logging
import requests
import voluptuous as vol

from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG,ATTR_OPTIONS
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEFAULT_LANG = 'zh'
SUPPORT_LANGUAGES = ['zh']

CONF_APIKEY = 'api_key'
CONF_SECRETKEY = 'secret_key'
CONF_SPEED = 'speed'
CONF_PITCH = 'pitch'
CONF_VOLUME = 'volume'
CONF_PERSON = 'person'

TOKEN_INTERFACE = 'https://openapi.baidu.com/oauth/2.0/token'
TEXT2AUDIO_INTERFACE = 'http://tsn.baidu.com/text2audio'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_APIKEY): cv.string,
    vol.Required(CONF_SECRETKEY): cv.string,
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_SPEED, default='5'): cv.string,
    vol.Optional(CONF_PITCH, default='5'): cv.string,
    vol.Optional(CONF_VOLUME, default='5'): cv.string,
    vol.Optional(CONF_PERSON, default='0'): cv.string,
})

def get_engine(hass, config):
    apiKey = config.get(CONF_APIKEY)
    secretKey = config.get(CONF_SECRETKEY)
    lang = config.get(CONF_LANG)
    speed = config.get(CONF_SPEED)
    pitch = config.get(CONF_PITCH)
    volume = config.get(CONF_VOLUME)
    person = config.get(CONF_PERSON)
    return BaiduTTS(apiKey, secretKey, lang, speed, pitch ,volume, person)

class BaiduTTS (Provider):
    def __init__(self, apiKey, secretKey, lang, speed, pitch, volume, person):
        self._apiKey = apiKey
        self._secretKey = secretKey
        self._lang = lang
        self._speed = speed
        self._pitch = pitch
        self._volume = volume
        self._person = person
        self._token = None  

    def get_token(self):
        resp = requests.get(TOKEN_INTERFACE, params={'grant_type': 'client_credentials', 'client_id': self._apiKey, 'client_secret': self._secretKey})
        resp.encoding = 'utf-8'
        if resp.status_code != 200:
            _LOGGER.error('Get token tttp error:%s', resp.status_code)
            return None

        token_json =  resp.json()

        if 'access_token' not in token_json:
            _LOGGER.error('json error.')
            return None
        return token_json['access_token']

    @property
    def default_language(self):
        """Default language."""
        return self._lang

    @property
    def supported_languages(self):
        """List of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_options(self):
        """Return list of supported options like voice, emotionen."""
        return ['speed', 'pitch', 'volume', 'person']

    def get_tts_audio(self, message, language, options=None):
        if self._token is None:
            self._token = self.get_token()
        if self._token is None:
            _LOGGER.error('Token is nil')
            return

        if options is None:
            person = self._person
            speed = self._speed
            pitch = self._pitch
            volume = self._volume
        else:
            person = options.get('person', self._person)
            speed = options.get('speed', self._speed)
            pitch = options.get("pitch", self._pitch)
            volume = options.get('volume', self._volume)
        params = {
            'tex': message,
            'lan': language,
            'tok': self._token,
            'ctp': '1',
            'cuid': 'HomeAssistant',
            'spd':speed,
            'pit': pitch,
            'vol': volume,
            'per': person
        }

        resp = requests.get(TEXT2AUDIO_INTERFACE, params=params)
        if resp.status_code != 200:
            _LOGGER.error('Text2Audio Error: %s', resp.status_code)
            return

        data = resp.content
        return ('mp3', data)
