from django.shortcuts import render
from django.http import HttpResponseRedirect
import re, os
from .models import Buch
from django.db import transaction
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
    
        buch = Buch.objects.create(bezeichnung=bezeichnung)
        buch.exlibris = exlibris
        for key in daten:
            if key in attributnamen:
                setattr(buch, attributnamen[key], daten[key])
        buch.save()
        
    return HttpResponseRedirect('/warenkorb/')
