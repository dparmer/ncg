# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-27 00:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0012_nflgame_game_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='active_wk_points',
            field=models.IntegerField(default=0, verbose_name='Current Week Points'),
        ),
    ]