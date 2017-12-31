# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-26 23:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0019_taskmanager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskmanager',
            name='repeat_nfl_score_update_id',
        ),
        migrations.AddField(
            model_name='taskmanager',
            name='task_id',
            field=models.CharField(default='default', max_length=255, verbose_name='task id for task'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='taskmanager',
            name='task_name',
            field=models.CharField(default='default', max_length=30, verbose_name='task name'),
            preserve_default=False,
        ),
    ]
