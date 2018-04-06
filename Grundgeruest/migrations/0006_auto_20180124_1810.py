# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-24 18:10
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Grundgeruest', '0005_auto_20171211_1421'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scholariumprofile',
            name='plz',
            field=models.CharField(blank=True, max_length=10, null=True, validators=[django.core.validators.RegexValidator('^[0-9]+$')]),
        ),
    ]