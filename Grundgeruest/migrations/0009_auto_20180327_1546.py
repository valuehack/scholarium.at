# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-27 15:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Grundgeruest', '0008_stufe_unterstuetzung'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unterstuetzung',
            old_name='user',
            new_name='profil',
        ),
    ]
