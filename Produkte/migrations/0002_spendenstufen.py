# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-03-10 15:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Produkte', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Spendenstufen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bezeichnung', models.CharField(max_length=30)),
                ('slug', models.SlugField(blank=True, max_length=30)),
                ('zeit_erstellt', models.DateTimeField(auto_now_add=True)),
                ('spendenbeitrag', models.SmallIntegerField()),
                ('beschreibung', models.TextField()),
                ('gegenwert1', models.TextField(blank=True, null=True)),
                ('gegenwert2', models.TextField(blank=True, null=True)),
                ('gegenwert3', models.TextField(blank=True, null=True)),
                ('gegenwert4', models.TextField(blank=True, null=True)),
                ('gegenwert5', models.TextField(blank=True, null=True)),
                ('gegenwert6', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Spendenstufen',
            },
        ),
    ]
