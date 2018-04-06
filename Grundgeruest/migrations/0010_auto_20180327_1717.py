# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-27 17:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Grundgeruest', '0009_auto_20180327_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unterstuetzung',
            name='stufe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Produkte.Spendenstufe'),
        ),
        migrations.DeleteModel(
            name='Stufe',
        ),
    ]