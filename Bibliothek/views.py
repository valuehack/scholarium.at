from django.shortcuts import render
from django.http import HttpResponseRedirect
import re, os
from . import models
from django.db import transaction
import sqlite3 as lite
from seite.settings import BASE_DIR

attributnamen = {
    'author': 'autor',
    'isbn': 'isbn',
    'title': 'titel', 
    'address': 'adresse',
    'edition': 'ausgabe',
    'publisher': 'herausgeber',
    'keywords': 'stichworte',
    'language': 'sprache',
    'note': 'notiz',
    'abstract': 'zusammenfassung',
    'series': 'serie',
    'year': 'jahr'}

@transaction.atomic
def aus_datei_einlesen(request, exlibris=''):
    f = open(os.path.join(BASE_DIR, 'buchliste'), 'r')
    text = f.read()[7:-2] # an die bibtex-Ausgabe von zotero angepasst
    f.close()

    trennung = re.compile('\}\n\n(?P<name>[@, \w]*)\{')
    liste = trennung.sub('XXX', text).split('XXX')
    for buch in liste:
        zeilen = buch.split(',\n\t')
        teilsplit = re.compile(r'(\w+) = \{(.*)\}')
        bezeichnung = zeilen[0]
        matches = [teilsplit.match(zeile) for zeile in zeilen[1:]]
        daten = dict([match.groups() for match in matches if match])
    
        buch = models.Buch.objects.create(bezeichnung=bezeichnung)
        buch.exlibris = exlibris
        for key in daten:
            if key in attributnamen:
                setattr(buch, attributnamen[key], daten[key])
        buch.save()
        
    return HttpResponseRedirect('/warenkorb/')


def alte_buecher_aus_db_einlesen():
    """ liest alte buecher mit Format 0001 (also nicht digital, fast alle) 
    aus alter db (als .sqlite exportiert) aus """
    
    # zuerst Artikel auslesen
    models.Altes_Buch.objects.all().delete()
    
    con = lite.connect(os.path.join(BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte where type is 'antiquariat' and format is '0001';")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for buch in zeilen:
            models.Altes_Buch.objects.create(
                bezeichnung=buch['id'],
                autor_und_titel=buch['title'],
                preis_kaufen=buch['price_book'],
                slug=buch['id'])

