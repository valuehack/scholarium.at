# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-05-11 08:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Veranstaltungen', '0006_auto_20170510_0046'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='medium',
            name='gehoert_zu',
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='anzahl_aufzeichnung',
            field=models.SmallIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='anzahl_livestream',
            field=models.SmallIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='datei',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='preis_aufzeichnung',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='veranstaltung',
            name='preis_livestream',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='Medium',
        ),
    ]