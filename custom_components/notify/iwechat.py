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
    Oct.14th 2017
'''

REQUIREMENTS = ['wxpy==0.3.9.8','pillow']

import logging
import os

from wxpy import *
import requests
import voluptuous as vol

from homeassistant.components.notify import (BaseNotificationService, ATTR_TARGET, ATTR_DATA, ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA)
from homeassistant.exceptions import (HomeAssistantError, TemplateError)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_IMAGE = 'image'
ATTR_VIDEO = 'video'
ATTR_FILE = 'file'

# For sending msg
GROUP_POSTFIX = '#group#'

CONF_TULING_API_KEY = 'tuling_api_key'
CONF_COMMANDER = 'commander'
CONF_CMD_HANDLER = 'cmd_handler'
CONF_CMD_PREFIX = 'cmd_prefix'
CONF_TTS_HANDLER = 'tts_handler'
CONF_TTS_PREFIX = 'tts_prefix'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_TULING_API_KEY): cv.string,
    vol.Optional(CONF_COMMANDER): cv.string,
    vol.Inclusive(CONF_CMD_HANDLER, 'cmd sys', 'Cmd handler and cmd prefix must exist together'): cv.entity_id,
    vol.Inclusive(CONF_CMD_PREFIX, 'cmd sys', 'Cmd handler and cmd prefix must exist together'): cv.string,
    vol.Inclusive(CONF_CMD_HANDLER, 'tts sys', 'Tts handler and tts prefix must exist together'): cv.entity_id,
    vol.Inclusive(CONF_CMD_PREFIX, 'tts sys', 'Tts handler and tts prefix must exist together'): cv.string,
})

def get_service(hass, config, discovery_info=None):
    # Imagine that the bot is your wechat client.
    tuling_api_key = config.get(CONF_TULING_API_KEY, None)
    commander = config.get(CONF_COMMANDER, None)
    cmd_handler = config.get(CONF_CMD_HANDLER, None)
    cmd_prefix = config.get(CONF_CMD_PREFIX, None)
    tts_handler = config.get(CONF_TTS_HANDLER, None)
    tts_prefix = config.get(CONF_TTS_PREFIX, None)

    cache_path = os.path.join(hass.config.path('deps'), 'wxpy.pkl')
    bot = Bot(cache_path=cache_path, console_qr=True)

    if commander is not None:
        commander = ensure_one(bot.friends().search(commander))

    def invoke_service(hdomain, hservice, data):
        hass.services.call(hdomain, hservice, data)
        hass.block_till_done()

    def handle_cmd(cmd_msg, chat):
        if cmd_handler is None:
            return
        try:
            items = cmd_handler.split('.')
            invoke_service(items[0], items[1], {'message': cmd_msg})
            chat.send_msg('Invoke cmd handler success.')
        except Exception as ex:
            chat.send_msg('Failed, try again or contant admin.')
            _LOGGER.exception(ex)

    def handle_tts(tts_msg, sender, sex, chat):
        if tts_handler is None:
            return
        try:
            items = tts_handler.split('.')
            invoke_service(items[0], items[1], {'message': tts_msg, 'sender': sender, 'sex': sex})
            chat.send_msg('Invoke tts handler success.')
        except Exception as ex:
            chat.send_msg('Failed, try again or contant admin.')
            _LOGGER.exception(ex)

    def is_specified_fmt(fmt_prefix, msg_text):
        if fmt_prefix is None:
            return False
        text = msg_text.lower()
        fmt_pf = fmt_prefix.lower()
        return text.startswith(fmt_pf)

    def is_cmd_fmt(msg_text):
        return is_specified_fmt(cmd_prefix, msg_text)

    def is_tts_fmt(msg_text):
        return is_specified_fmt(tts_prefix, msg_text)

    @bot.register(Friend)
    def on_msg_received(msg):
        # If it is sent by specified user, check if it is a cmd
        if commander is not None and msg.sender == commander:
            # If it matches cmd fmt, invoke cmd handler to process
            if is_cmd_fmt(msg.text):
                if cmd_handler is not None:
                    handle_cmd(msg.text, msg.chat)
                else:
                    msg.chat.send_msg('Unsupport: No cmd handler specified.')
                return
        # If it matches tts fmt, invoke tts handler to process
        if is_tts_fmt(msg.text):
            if tts_handler is not None:
                handle_tts(msg.text, msg.sender.remark_name, msg.sender.sex, msg.chat)
            else:
                msg.chat.send_msg('Unsupport: No tts handler specified.')
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
                if tar == '':
                    _LOGGER.error('Invalid target.')
                    continue
                # Determine the target is a friend or group.
                target = tar.split(GROUP_POSTFIX)
                if len(target) == 1:
                    chats = self.bot.friends().search(target[0])
                else:
                    chats = self.bot.groups().search(target[0])
                chats_count = len(chats)
                if chats is not None and chats_count > 0:
                    # Only send to the first chat matched specified target.
                    chat = chats[0]
                    if data is not None:
                        if ATTR_IMAGE in data:
                            image = data.get(ATTR_IMAGE, None)
                            chat.send_image(image)
                        elif ATTR_VIDEO in data:
                            video = data.get(ATTR_VIDEO, None)
                            chat.send_video(video)
                        elif ATTR_FILE in data:
                            file = data.get(ATTR_FILE, None)
                            chat.send_file(file)
                        else:
                            _LOGGER.error('No image, video or file in data.')
                    chat.send_msg(message)
                else:
                    _LOGGER.error('Incorrect name of friend or group: %s', target[0])
