# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import NflGameMgr, NflGame
import time


@shared_task
def task_nfl_score_update():
    NflGameMgr.game_score_update2()

@shared_task
def repeat_nfl_score_update():

    repeat = True
    while repeat:
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        NflGameMgr.game_score_update2()
        time.sleep(60)
        for game in NflGame.objects.filter(season=season, week=week):
            if game.game_status == 'Scheduled' or game.game_status == 'Final':
                repeat = False
            else:
                repeat = True
                continue

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)