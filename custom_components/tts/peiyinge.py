'''
# Module name:
    peiyinge.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests.

# Purpose:
    Peiyinge tts powered by Iflytek.

# Author:
    Lidicn, Retroposter retroposter@outlook.com
    Retroposter copied from lidicn's iflytek.py.

# Created:
    Sep.30th 2017

# Last Modified:
    Sep.30th 2017
'''

import logging
import json
import os
import urllib
import urllib.parse
import requests
import voluptuous as vol

from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG,ATTR_OPTIONS
import homeassistant.helpers.config_validation as cv


_LOGGER=logging.getLogger(__name__)

DEFAULT_LANG = 'zh'
SUPPORT_LANGUAGES = [
    'zh',
]

CONF_PERSON_ID = 'person_id'
CONF_LANG = 'lang'
CONF_SPEED = 'speed'
CONF_VOLUME = 'volume'

TOKEN_API  = 'http://www.peiyinge.com/make/getSynthSign'
TEXT2AUDIO_API_FMT = 'http://proxy.peiyinge.com:17063/synth?ts={0}&sign={1}&vid={2}&speed={3}&volume={4}&content={5}'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PERSON_ID, default=None): cv.string,
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_SPEED, default='5'): cv.string,
    vol.Optional(CONF_VOLUME, default='5'): cv.string,
})

def get_engine(hass, config):
    person_id = config.get(CONF_PERSON_ID)
    lang = config.get(CONF_LANG)
    speed = config.get(CONF_SPEED)
    volume = config.get(CONF_VOLUME)
    return PeiyingeTTS(person_id, lang, speed, volume)


class PeiyingeTTS (Provider):
    def __init__(self, lang, person_id, speed, volume):
        self._lang = lang
        self._person_id = person_id  
        self._speed = speed
        self._volume = volume

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
        return ['person_id', 'speed', 'volume']
    
    def get_tts_audio(self, message, language, options=None):
        if options == None:
            person_id = self._person_id
            speed = self._speed
            volume = self._volume
        else:
            person_id = options.get(CONF_PERSON_ID, self._person_id)
            speed = options.get(CONF_SPEED, self._speed)
            volume = options.get(CONF_VOLUME, self._volume)
        data = self.message_to_tts(message, person_id, speed, volume)
        return ('mp3',data)

    def message_to_tts(self, message, person_id, speed, volume):
        msg = message.encode('utf8')
        data = {
            'content': msg
        }
        result_info = requests.post(TOKEN_API, data=data).json()
        ts = result_info['ts']
        sign = result_info['sign']
        content = urllib.parse.quote(msg)
        voice_url = TEXT2AUDIO_API_FMT.format(ts, sign, person_id, speed, volume, content)
        rep = requests.get(voice_url)
        data = rep.content
        return data
