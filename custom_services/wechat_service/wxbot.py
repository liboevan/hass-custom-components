'''
# Module name:
    wxbot.py

# Prerequisite:
    Based on Python 3.4
    Need python module pillow and wxpy.

# Purpose:
    An independent wechat service based on Wxpy for hass component wechat3.py.

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Nov.22th 2017

# Last Modified:
    Nov.22th 2017
'''

REQUIREMENTS = ['wxpy==0.3.9.8','pillow']

import configparser
import json
import logging
import os
import socket

from wxpy import *

# No attribute config???
#logging.config.fileConfig('logging.conf')
_LOGGER = logging.getLogger('wxbot')

ATTR_TARGET = 'target'
ATTR_MESSAGE = 'message'
ATTR_DATA = 'data'

ATTR_IMAGE = 'image'
ATTR_VIDEO = 'video'
ATTR_FILE = 'file'

GROUP_POSTFIX = '#group#'

SERVICE_PORT = 18001
CUSTOMER_PORT = 18002

is_running = False

def get_config_value(conf, section, option, default=''):
    try:
        value = conf.get(section, option)
    except:
        value = default
    return value

def run_service():
    is_running = True
    conf = configparser.ConfigParser()
    conf.read('config.conf')
    tuling_api_key = get_config_value(conf, 'bot', 'tuling_api_key')
    cmder = get_config_value(conf, 'cmd', 'cmder')
    cmd_prefix = get_config_value(conf, 'cmd', 'cmd_prefix')
    tts_prefix = get_config_value(conf, 'cmd', 'tts_prefix')

    cache_path = os.path.join(os.getcwd(), 'wxpy.pkl')
    bot = Bot(cache_path=cache_path, console_qr=True)

    if cmder != '':
        try:
            cmder = ensure_one(bot.friends().search(cmder))
        except:
            _LOGGER.error('Failed to set commander: no friend named %s.', cmder)
            cmder = None
    def process_special_msg(msg, msg_type, sender, sex, chat):
        msg_data = {'msg_type': msg_type, 'message': msg, 'sender': sender, 'sex': sex}
        msg_to_send = json.dumps(msg_data)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', CUSTOMER_PORT))
            sock.send(msg_to_send.encode())
            sock.close()
            replay = '{0} msg: {1} was sent successfully.'.format(msg_type, msg)
        except Exception as ex:
            replay = '{0} msg: {1} failed to be sent.'.format(msg_type, msg)
            _LOGGER.exception(ex)
        chat.send_msg(replay)

    def is_specified_fmt(fmt_prefix, msg_text):
        if fmt_prefix is None or msg_text is None:
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
        if msg.text is not None:
            # If it is sent by specified user, check if it metches cmd fmt. If it does,
            # invoke cmd handler to process
            if cmder is not None and msg.sender == cmder and is_cmd_fmt(msg.text):
                # If it matches cmd fmt
                process_special_msg(msg.text, 'cmd', msg.sender.remark_name, msg.sender.sex, msg.chat)
                return
            # If it matches tts fmt
            if is_tts_fmt(msg.text):
                process_special_msg(msg.text, 'tts', msg.sender.remark_name, msg.sender.sex, msg.chat)
                return
        if tuling_api_key != '':
            tuling = Tuling(api_key=tuling_api_key)
            tuling.do_reply(msg)

    wechat_service = WeChatService(bot)

    def process_buffer(msg_bytes):
        try:
            msg_str = str(msg_bytes, encoding='utf8')
            json_obj = json.loads(msg_str)
            target = json_obj.get(ATTR_TARGET)
            message = json_obj.get(ATTR_MESSAGE)
            data = json_obj.get(ATTR_DATA)
            wechat_service.send_message(message, target=target, data=data)
        except Exception as ex:
            _LOGGER.error('Something wrong when processing msg.')
            _LOGGER.exception(ex)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', SERVICE_PORT))
    sock.listen(5)
    while True:
        conn, addr = sock.accept()
        try:
            conn.settimeout(50)
            buf = conn.recv(1024)
            process_buffer(buf)
        except socket.timeout:
            _LOGGER.error('Conn timeout.')
        conn.close()

class WeChatService():
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

if __name__ == '__main__':
    if not is_running:
        run_service()
    else:
        _LOGGER.warning('It is running.')
