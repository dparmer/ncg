# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-26 15:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0010_entry_is_locked'),
    ]

    operations = [
        migrations.AddField(
            model_name='nflgame',
            name='in_progress',
            field=models.BooleanField(default=False, verbose_name='Game In Progress'),
        ),
    ]
