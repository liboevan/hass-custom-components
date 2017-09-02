'''
# Module name:
    wechat.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests and wxpy.

# Purpose:
    Wechat notify powered by wxpy

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Aug.30th 2017
'''

REQUIREMENTS = ['wxpy==0.3.9.8','pillow']

import logging
import os
import voluptuous as vol
import xml.etree.ElementTree as ET

from wxpy import *
import requests

from homeassistant.components.notify import (BaseNotificationService, ATTR_TARGET, ATTR_DATA, ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_IMAGE = 'image'
ATTR_VIDEO = 'video'
ATTR_FILE = 'file'

GROUP_POSTFIX = '#group#'

def get_service(hass, config, discovery_info=None):
    # Imagine that the bot is your wechat client.
    cache_path = os.path.join(hass.config.path('deps'), 'wxpy.pkl')
    bot = Bot(cache_path=cache_path, console_qr=True)
    return WeChatService(bot)

class WeChatService(BaseNotificationService):
    def __init__(self, bot):
        """Initialize the service."""
        self.bot = bot

    def send_message(self, message="", **kwargs):
        targets = kwargs.get(ATTR_TARGET)
        data = kwargs.get(ATTR_DATA)

        # Send to file helper if no target specified.
        if targets is None:
            if data is not None:
                if ATTR_IMAGE in data:
                    image = data.get(ATTR_IMAGE, None)
                    self.bot.file_helper.send_image(image)
                elif ATTR_VIDEO in data:
                    video = data.get(ATTR_VIDEO, None)
                    self.bot.file_helper.send_video(video)
                elif ATTR_FILE in data:
                    file = data.get(ATTR_FILE, None)
                    self.bot.file_helper.send_file(file)
                else:
                    _LOGGER.error('No image, video or file in data.')
            self.bot.file_helper.send_msg(message)
        else:
            for tar in targets:
                if tar == "":
                    _LOGGER.error('Invalid target.')
                    continue
                # Determine the target is a friend or group.
                target = tar.split(GROUP_POSTFIX)
                if len(target) == 1:
                    chats = self.bot.friends().search(target[0])
                else:
                    chats = self.bot.groups().search(target[0])
                if chats is not None and len(chats) > 0:
                    # Only send to the first chat matched specified target.
                    chat = chats[0]
                    if data is not None:
                        if ATTR_IMAGE in data:
                            image = data.get(ATTR_IMAGE,None)
                            chat.send_image(image)
                        elif ATTR_VIDEO in data:
                            video = data.get(ATTR_VIDEO,None)
                            chat.send_video(video)
                        elif ATTR_FILE in data:
                            file = data.get(ATTR_FILE,None)
                            chat.send_file(file)
                        else:
                            _LOGGER.error('No image, video or file in data.')
                    chat.send_msg(message)
                else:
                    _LOGGER.error('Incorrect name of friend or group: %s', target[0])
