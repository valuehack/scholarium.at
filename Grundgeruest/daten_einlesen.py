import os, shutil
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein
from Veranstaltungen.models import Veranstaltung, ArtDerVeranstaltung, Studiumdings

import pdb    

try:
    os.chdir('/home/scholarium/godaddy_daten/')
except FileNotFoundError:
    pass

def buechlein_ebooks_einlesen():
    """ Kopiert die pdfs/epub/mobi der scholienbuechlein aus dem 
    input-Ordner nach media, verändert sicherheitshalber den Dateinamen, 
    und speichert den link in der db """
    buechlein = Buechlein.objects.all()
    liste_ext = ['jpg', 'pdf', 'mobi', 'epub']
    
    for b in buechlein:
        for ext in liste_ext:
            nachordner = os.path.join(MEDIA_ROOT, 'scholienbuechlein/')
            if not os.path.exists(nachordner):
                os.makedirs(nachordner)
            dateifeld = b.bild if ext=='jpg' else getattr(b, ext)
            if dateifeld and dateifeld.name.split('/')[-1] in os.listdir(nachordner):
                continue
            else:
                von_ordner = 'schriften/' if ext=='jpg' else 'down_secure/content_secure/'
                von = '%s%s.%s' % (von_ordner, b.slug, ext)
                name_neu = '%s_%s.%s' % (b.slug, Nutzer.erzeuge_zufall(8, 2), ext)
                dateifeld.name = 'scholienbuechlein/%s' % name_neu
                shutil.copy2(von, os.path.join(MEDIA_ROOT, dateifeld.name))
                if not ext == 'jpg':
                    setattr(b, 'ob_' + ext, True)

            b.save()
        

def veranstaltungen_aus_db():
    """ liest veranstaltungen aus alter db (als .sqlite exportiert) aus 
    !! Achtung, löscht davor die aktuellen Einträge !! """
    
    from django.db import transaction
    import sqlite3 as lite
    from django.conf import settings
    import os, pdb
    from django.http import HttpResponseRedirect
    
    # Seminare, Salons, Vorlesungen, Vorträge einlesen
    Veranstaltung.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte WHERE type in ('salon'," + 
            " 'seminar', 'media-vortrag', 'media-vorlesung');")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
    
    arten = {'salon': ArtDerVeranstaltung.objects.get(
            bezeichnung='Salon'),
        'seminar': ArtDerVeranstaltung.objects.get(
            bezeichnung='Seminar'),
        'media-vortrag': ArtDerVeranstaltung.objects.get(
            bezeichnung='Vortrag'),
        'media-vorlesung': ArtDerVeranstaltung.objects.get(
            bezeichnung='Vorlesung'),}
    
    with transaction.atomic():
        for zeile in zeilen:
            if zeile['type'] in ['seminar', 'salon']:
                datum = zeile['start'] or '1111-01-01 00-00'
            else:
                if zeile['last_donation'] in ['0000-00-00 00:00:00', None]:
                    datum = '1111-01-01 00-00'
                else:
                    datum = zeile['last_donation']
                    
            datum = datum.split(' ')[0]
            v = Veranstaltung.objects.create(
                bezeichnung=zeile['title'],
                slug=zeile['id'],
                beschreibung=zeile['text'],
                art_veranstaltung=arten[zeile['type']],
                datum=datum, 
                link=zeile['livestream'])
            if zeile['livestream']: 
                v.ob_livestream = True
                v.save()

    # Studiendinger einlesen
    Studiumdings.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte WHERE type='programm';")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
        
    with transaction.atomic():
        for zeile in zeilen:
            dings = Studiumdings.objects.create(
                bezeichnung=zeile['title'],
                slug=zeile['id'],
                beschreibung1=zeile['text'],
                beschreibung2=zeile['text2'],
                preis_teilnahme=zeile['price'],)


def mediendateien_einlesen():
    von_ordner = 'down_secure/content_secure/'
    nach_ordner = os.path.join(MEDIA_ROOT, 'veranstaltungen_mp3')
    if not os.path.exists(nach_ordner):
        os.makedirs(nach_ordner)
    for v in Veranstaltung.objects.all():
        von_name = 'medien-'+v.slug+'.mp3'
        dateifeld = getattr(v, 'datei')
        if dateifeld and dateifeld.name.split('/')[-1] in os.listdir(nach_ordner):
            continue
        if von_name in os.listdir(von_ordner):
            von = von_ordner + von_name
            dateiname = '%s_%s.mp3' % (v.slug, Nutzer.erzeuge_zufall(8, 2))
            dateifeld.name = 'veranstaltungen_mp3/' + dateiname
            shutil.copy2(von, os.path.join(MEDIA_ROOT, dateifeld.name))
            v.ob_aufzeichnung = True  
            v.save()

