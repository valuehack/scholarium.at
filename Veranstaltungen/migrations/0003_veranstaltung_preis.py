# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-05-08 14:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Veranstaltungen', '0002_medium_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='veranstaltung',
            name='preis',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]