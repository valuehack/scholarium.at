# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-04 17:06
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
                ('bezeichnung', models.CharField(max_length=30)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('beschreibung', models.TextField(blank=True, max_length=1200, null=True)),
                ('preis_praesenz', models.SmallIntegerField()),
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
            name='Medium',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=30)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('datei', models.FileField(upload_to='')),
                ('typ', models.CharField(blank=True, max_length=30, null=True)),
                ('beschreibung', models.TextField(blank=True, max_length=2000, null=True)),
                ('datum', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Medien',
            },
        ),
        migrations.CreateModel(
            name='Veranstaltung',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=30)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('beschreibung', models.TextField(max_length=2000)),
                ('datum', models.DateField()),
                ('art_veranstaltung', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Veranstaltungen.ArtDerVeranstaltung')),
            ],
            options={
                'verbose_name_plural': 'Veranstaltungen',
            },
        ),
        migrations.AddField(
            model_name='medium',
            name='gehoert_zu',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Veranstaltungen.Veranstaltung'),
        ),
    ]
