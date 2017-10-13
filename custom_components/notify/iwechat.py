'''
# Module name:
    iwechat.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests, pillow and wxpy.

# Purpose:
    Advanced wechat notifier (based on wechat.py) powered by Wxpy and Wechat.

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Oct.12th 2017

# Last Modified:
    Oct.13th 2017
'''

REQUIREMENTS = ['wxpy==0.3.9.8','pillow']

import logging
import os

from wxpy import *
import requests
import voluptuous as vol

from homeassistant.components.notify import (BaseNotificationService, ATTR_TARGET, ATTR_DATA, ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_IMAGE = 'image'
ATTR_VIDEO = 'video'
ATTR_FILE = 'file'

GROUP_POSTFIX = '#group#'

CONF_TULING_API_KEY = 'tuling_api_key'
CONF_COMMANDER = 'commander'
CONF_CMD_HANDLER = 'cmd_handler'
CONF_CMD_PREFIX = 'cmd_prefix'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_TULING_API_KEY): cv.string,
    vol.Optional(CONF_COMMANDER): cv.string,
    vol.Optional(CONF_CMD_HANDLER): cv.entity_id,
    vol.Optional(CONF_CMD_PREFIX): cv.string,
})

def get_service(hass, config, discovery_info=None):
    # Imagine that the bot is your wechat client.
    tuling_api_key = config.get(CONF_TULING_API_KEY, None)
    commander = config.get(CONF_COMMANDER, None)
    cmd_handler = config.get(CONF_CMD_HANDLER, None)
    cmd_prefix = config.get(CONF_CMD_PREFIX, None)

    cache_path = os.path.join(hass.config.path('deps'), 'wxpy.pkl')
    bot = Bot(cache_path=cache_path, console_qr=True)

    if commander is not None:
        commander = ensure_one(bot.friends().search(commander))

    def handle_cmd(msg_text):
        if cmd_handler is None:
            return
        try:
            items = cmd_handler.split('.')
            hass.services.call(items[0], items[1], {'message': msg_text})
            hass.block_till_done()
        except:
            _LOGGER.error('Handle cmd error: %s', msg_text)

    def is_cmd_fmt(msg_text):
        if cmd_prefix is None:
            return False
        text = msg_text.lower()
        cmd_pf = cmd_prefix.lower()
        return text.startswith(cmd_pf)

    @bot.register(Friend)
    def on_msg_received(msg):
        # If it was sent by specified user
        if commander is not None and msg.sender == commander:
            msg_text = msg.text
            # If it matches specified fmt
            if is_cmd_fmt(msg_text):
                if cmd_handler is None:
                    msg.chat.send_msg('No command handler specified.')
                else:
                    handle_cmd(msg.text)
                return
        if tuling_api_key is not None:
            tuling = Tuling(api_key=tuling_api_key)
            tuling.do_reply(msg)

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
