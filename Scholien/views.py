from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from Grundgeruest.views import DetailMitMenue, ListeMitMenue, TemplateMitMenue
from . import models

from django.db import transaction
import sqlite3 as lite

from django.conf import settings
import os, pdb

# Create your views here.

def liste_artikel(request):
    """ Gibt Übersichtsseite mit Artikeln aus; oder, wenn GET-Daten da
    sind, ein Detail-view zu dem Artikel (rückwärtskompatibel) """
    
    slug = request.GET.get('q')
    if slug: # erst prüfen, ob was da ist
        return ein_artikel(request, slug)
    
    # nur wenn kein 'q' im GET, wird Liste ausgegeben:    
    if request.user.is_authenticated() and request.user.hat_guthaben():
        return ListeMitMenue.as_view(
            model=models.Artikel,
            template_name='Scholien/liste_artikel.html',
            context_object_name='liste_artikel',
            paginate_by = 5)(request)
    elif request.user.is_authenticated():
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien_angemeldet.html', 
            )(request)         
    else:
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien.html', 
            )(request) 
            
def liste_buechlein(request):
    if request.user.is_authenticated() and request.user.hat_guthaben():
        return ListeMitMenue.as_view(
            model=models.Buechlein,
            template_name='Scholien/liste_buechlein.html',
            context_object_name='buechlein',
            paginate_by = 5)(request)
    else:
        # im Template wird Kleinigkeit unterschieden: 
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien.html', 
            )(request)             


def ein_artikel(request, slug):
    return DetailMitMenue.as_view(
        template_name='Scholien/detail.html',
        model=models.Artikel,
        context_object_name = 'scholie')(request, slug=slug)

def ein_buechlein(request, slug):
    return DetailMitMenue.as_view(
        template_name='Scholien/detail_buechlein.html',
        model=models.Buechlein,
        context_object_name = 'scholienbuechlein')(request, slug=slug)

def daten_einlesen(request):
    aus_alter_db_einlesen()
    return HttpResponseRedirect('/scholien')
    

def aus_alter_db_einlesen():
    """ liest scholienartikel und scholienbuechlein aus alter db (als 
    .sqlite exportiert) aus 
    !! Achtung, löscht davor die aktuellen Einträge !! """
    
    # zuerst Artikel auslesen
    models.Artikel.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM blog;")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for scholie in zeilen:
            if scholie['publ_date'] == '0000-00-00':
                scholie['publ_date'] = '1111-01-01'
            models.Artikel.objects.create(
                bezeichnung=scholie['title'],
                inhalt=scholie['public_text'],
                inhalt_nur_fuer_angemeldet=scholie['private_text'],
                datum_publizieren=scholie['publ_date'], 
                slug=scholie['id'])

    # und Büchlein auslesen
    # es fehlt einiges, insb. die pdfs einzutragen
    models.Buechlein.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte WHERE type='scholie';")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for scholie in zeilen:
            buch = models.Buechlein.objects.create(
                bezeichnung=scholie['title'],
                beschreibung=scholie['text'],
                alte_nr=scholie['n'], 
                slug=scholie['id'])
            
            dateiname = scholie['id']+'.jpg'
            buch.bild_holen(
                'http://www.scholarium.at/schriften/'+dateiname,
                dateiname)
            buch.save()
