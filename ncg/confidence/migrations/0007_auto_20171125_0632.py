# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-25 12:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confidence', '0006_auto_20171124_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='is_winner',
            field=models.NullBooleanField(verbose_name='Winner'),
        ),
    ]