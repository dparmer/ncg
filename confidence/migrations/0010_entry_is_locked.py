# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-25 18:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0009_player_latest_entry_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='is_locked',
            field=models.BooleanField(default=False, verbose_name='Entry Locked'),
        ),
    ]
