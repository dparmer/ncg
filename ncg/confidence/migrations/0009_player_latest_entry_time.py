# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-25 14:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0008_player_has_current_entry'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='latest_entry_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last Entry'),
        ),
    ]