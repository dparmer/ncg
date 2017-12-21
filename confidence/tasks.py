# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import NflGameMgr


@shared_task
def task_nfl_score_update():
    NflGameMgr.game_score_update()

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)