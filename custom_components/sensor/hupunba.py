'''
# Module name:
    hupunba.py

# Prerequisite:
    Based on Python 3.4
    Need python module requests and bs4

# Purpose:
    NBA game sensor powered by Hupu and NBA

# Author:
    Retroposter retroposter@outlook.com

# Created:
    Oct.24th 2017

# Last Modified:
    Oct.25th 2017
'''

from datetime import date, timedelta
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

DEFAULT_NAME = 'NBA'
ATTRIBUTION = 'Powered by Hupu'

PAT_SCORE = re.compile('\d+')
DEFAULT_TEAM = 'lakers'
RESULTS = ['胜', '负']

DATA_MY_SCORE = 'my score'
DATA_OPPONENT_SCORE = 'opponent score'
DATA_OPPONENT = 'opponent'
DATA_RESULT = 'result'
DATA_GAME_TIME = 'game time'
DATA_IS_MY_HOME = 'is my home'
DATA_GAME_ID = 'game id'

CONF_UPDATE_INTERVAL = 'update_interval'
CONF_MY_TEAM = 'my_team'

TEAM_MAP = {
    'grizzlies': '灰熊',
    'spurs': '马刺',
    'ockets': '火箭',
    'pelicans': '鹈鹕',
    'mavericks': '小牛',

    'clippers': '快船',
    'warriors': '勇士',
    'lakers': '湖人',
    'suns': '太阳',
    'kings': '国王',

    'timberwolves': '森林狼',
    'jazz': '爵士',
    'blazers': '开拓者',
    'nuggets': '掘金',
    'thunder': '雷霆',

    'raptors': '猛龙',
    'nets': '篮网',
    'celtics': '凯尔特人',
    '76ers': '76人',
    'knicks': '尼克斯',

    'wizards': '奇才',
    'magic': '魔术',
    'heat': '热火',
    'hornets': '黄蜂',
    'hawks': '老鹰',

    'bucks': '雄鹿',
    'cavaliers': '骑士',
    'pistons': '活塞',
    'pacers': '步行者',
    'bulls': '公牛'
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_MY_TEAM, default=DEFAULT_TEAM): vol.All(cv.ensure_list, [vol.In(TEAM_MAP)]),
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(minutes=15)): (vol.All(cv.time_period, cv.positive_timedelta)),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    interval = config.get(CONF_UPDATE_INTERVAL)
    my_team = config.get(CONF_MY_TEAM)
    hupunba_data = HupuNbaData(my_team, interval)
    hupunba_data.update()
    # If connection failed don't setup platform.
    if hupunba_data.data is None:
        _LOGGER.error('hupunba_data.data is None, will not generate sensor.')
        return False
    add_devices([HupuNbaSensor(hass, hupunba_data, my_team)], True)


class HupuNbaSensor(Entity):
    def __init__(self, hass, hupunba_data, my_team):
        """Initialize the sensor."""
        self.hupunba_data = hupunba_data
        self.my_team = my_team
        self.entity_id = generate_entity_id('sensor.{}', self.my_team, hass=hass)
        self.display_name = self.my_team.capitalize()
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
        return 'mdi:gamepad-variant'

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        data = self.hupunba_data.data
        if data is not None:
            attrs['start at'] = data[DATA_GAME_TIME]
            attrs['result'] = data[DATA_RESULT]
            if data[DATA_GAME_ID] is not None:
                attrs['boxscore'] = self.hupunba_data.boxscore_url
                attrs['recap'] = self.hupunba_data.recap_url
        return attrs

    def update(self):
        self.hupunba_data.update()
        data = self.hupunba_data.data
        if data is not None:
            my_score = data[DATA_MY_SCORE]
            opponent_score = data[DATA_OPPONENT_SCORE]
            opponent = data[DATA_OPPONENT]
            is_my_home = data[DATA_IS_MY_HOME]
            if is_my_home:
                symbol = 'VS'
            else:
                symbol = '@'
            self._state = '{0} {1} {2} {3} {4}'.format(TEAM_MAP[self.my_team], my_score,
                                                       symbol, opponent_score, opponent)


class HupuNbaData(object):
    def __init__(self, my_team, internal):
        self.my_team = my_team
        self.data = None
        self._home_url = 'https://nba.hupu.com/'
        self._sub_schedule_url = 'schedule/'
        self._sub_boxscore_url = 'games/boxscore/'
        self._sub_recap_url = 'games/recap/'
        # Apply throttling to methods using configured interval
        self.update = Throttle(internal)(self._update)

    @property
    def boxscore_url(self):
        if self.data is None or self.data[DATA_GAME_ID] is None:
            return None
        game_id = self.data[DATA_GAME_ID]
        return self._home_url + self._sub_boxscore_url + game_id

    @property
    def recap_url(self):
        if self.data is None or self.data[DATA_GAME_ID] is None:
            return None
        game_id = self.data[DATA_GAME_ID]
        return self._home_url + self._sub_recap_url + game_id

    def _update(self):
        rep = requests.get(self._home_url + self._sub_schedule_url+ self.my_team)
        soup = BeautifulSoup(rep.text, 'html.parser')
        schedule_soup = soup.find('table', class_='players_table')
        the_day = date.today()
        game_data = self._get_game_of_day(schedule_soup, the_day)
        retry = 0
        while game_data is None:
            the_day += timedelta(days=-1)
            game_data = self._get_game_of_day(schedule_soup, the_day)
            retry += 1
            if retry > 5:
                break
        if game_data is None or game_data == 'error':
            _LOGGER.error('Failed to get the game on %s, game data: %s', the_day, game_data)
            return
        self.data = game_data

    def _get_game_of_day(self, schedule_soup, day):
        day_str = day.strftime('%Y-%m-%d')
        pat_day = re.compile(day_str)
        day_tb = schedule_soup.find('td', text=pat_day)
        if day_tb is None:
            return None
        try:
            game_time = day_tb.text
            game_tr = day_tb.find_parent('tr')
            teams = game_tr.find('td')
            guest_team = teams.find('a')
            if guest_team.text == TEAM_MAP[self.my_team]:
                is_my_home = False
                opponent = guest_team.find_next('a').text
            else:
                is_my_home = True
                opponent = guest_team.text
            scores = teams.find_next('td')
            scores_list = re.findall(PAT_SCORE, scores.text)
            is_start = len(scores_list) > 1
            if is_start:
                if is_my_home:
                    opponent_score = scores_list[0]
                    my_team_score = scores_list[1]
                else:
                    my_team_score = scores_list[0]
                    opponent_score = scores_list[1]
            else:
                my_team_score = opponent_score = 0
            result = scores.find_next('td').text.strip()
            if result not in RESULTS:
                result = 'N/A'
            next_to_gtime = day_tb.find_next('a')
            if next_to_gtime.text == '数据统计':
                game_id = next_to_gtime['href'].strip(self._home_url + self._sub_boxscore_url)
            else:
                game_id = None
            return {DATA_MY_SCORE: my_team_score,
                    DATA_OPPONENT_SCORE: opponent_score,
                    DATA_OPPONENT: opponent,
                    DATA_RESULT: result,
                    DATA_GAME_TIME: game_time,
                    DATA_IS_MY_HOME: is_my_home,
                    DATA_GAME_ID: game_id}
        except:
            return 'error'
