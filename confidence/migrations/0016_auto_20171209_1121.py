# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-09 17:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0015_nflteam_alias'),
    ]

    operations = [
        migrations.AddField(
            model_name='nflgame',
            name='away_team_line',
            field=models.FloatField(default=0, null=True, verbose_name='Away Team Line'),
        ),
        migrations.AddField(
            model_name='nflgame',
            name='home_team_line',
            field=models.FloatField(default=0, null=True, verbose_name='Home Team Line'),
        ),
    ]
