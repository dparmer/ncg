# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-26 15:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0011_nflgame_in_progress'),
    ]

    operations = [
        migrations.AddField(
            model_name='nflgame',
            name='game_status',
            field=models.CharField(default='Scheduled', max_length=15, verbose_name='Game Status'),
        ),
    ]
