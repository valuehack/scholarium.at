# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-14 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Scholien', '0005_auto_20171106_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='artikel',
            name='prioritaet',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
