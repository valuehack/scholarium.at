# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-26 01:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArtDerVeranstaltung',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('beschreibung', models.TextField(blank=True, max_length=1200, null=True)),
                ('preis_teilnahme', models.SmallIntegerField()),
                ('preis_livestream', models.SmallIntegerField(blank=True, null=True)),
                ('preis_aufzeichnung', models.SmallIntegerField(blank=True, null=True)),
                ('max_teilnehmer', models.SmallIntegerField(blank=True, null=True)),
                ('zeit_beginn', models.TimeField()),
                ('zeit_ende', models.TimeField()),
            ],
            options={
                'verbose_name_plural': 'Arten der Veranstaltungen',
            },
        ),
        migrations.CreateModel(
            name='Studiumdings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('beschreibung1', models.TextField()),
                ('beschreibung2', models.TextField()),
                ('reihenfolge', models.SmallIntegerField(null=True)),
                ('preis_buchung', models.SmallIntegerField(blank=True, null=True)),
                ('anzahl_buchung', models.SmallIntegerField(blank=True, default=0)),
            ],
            options={
                'ordering': ['reihenfolge'],
                'verbose_name_plural': 'Studienprogramme',
                'verbose_name': 'Studienprogramm',
            },
        ),
        migrations.CreateModel(
            name='Veranstaltung',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('beschreibung', models.TextField()),
                ('beschreibung2', models.TextField(blank=True, null=True)),
                ('datum', models.DateField()),
                ('datei', models.FileField(blank=True, null=True, upload_to='')),
                ('link', models.URLField(blank=True, null=True)),
                ('ob_chat_anzeigen', models.BooleanField(default=False)),
                ('preis_teilnahme', models.SmallIntegerField(blank=True, null=True)),
                ('anzahl_teilnahme', models.SmallIntegerField(blank=True, default=0)),
                ('preis_livestream', models.SmallIntegerField(blank=True, null=True)),
                ('ob_livestream', models.BooleanField(default=0)),
                ('preis_aufzeichnung', models.SmallIntegerField(blank=True, null=True)),
                ('ob_aufzeichnung', models.BooleanField(default=0)),
                ('art_veranstaltung', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Veranstaltungen.ArtDerVeranstaltung')),
            ],
            options={
                'verbose_name_plural': 'Veranstaltungen',
                'verbose_name': 'Veranstaltung',
            },
        ),
    ]
