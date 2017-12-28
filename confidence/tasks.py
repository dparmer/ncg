# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import NflGameMgr, NflGame
import time


@shared_task
def task_nfl_score_update():
    NflGameMgr.game_score_update2()

@shared_task
def task_nfl_score_update2():
    NflGameMgr.game_score_update()

@shared_task
def repeat_nfl_score_update():
    repeat = True
    while repeat:
        NflGameMgr.game_score_update2()
        time.sleep(60)
        repeat = NflGame.is_active_games()

@shared_task
def add(x, y):
    time.sleep(60)
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)