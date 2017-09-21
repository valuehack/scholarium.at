import os, shutil
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein
from Bibliothek.models import Altes_Buch
from Veranstaltungen.models import Veranstaltung, ArtDerVeranstaltung, Studiumdings
from Produkte.models import Kauf

from django.db import transaction
import sqlite3 as lite

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
    
    con = lite.connect(os.path.join(BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte WHERE type in ('salon'," + 
            " 'media-salon', 'seminar', 'media-vortrag', 'media-vorlesung');")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
    
    arten = {'salon': ArtDerVeranstaltung.objects.get(
            bezeichnung='Salon'),
        'media-salon': ArtDerVeranstaltung.objects.get(
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
    
    con = lite.connect(os.path.join(BASE_DIR, 'alte_db.sqlite3'))
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


def mitwirkende_aus_db():
    """ liest Mitwirkende aus alter db (als .sqlite exportiert) aus 
    !! Achtung, löscht davor die aktuellen Einträge !! """
    
    Mitwirkende.objects.all().delete()
    
    con = lite.connect(os.path.join(BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM crew;")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for person in zeilen:
            neu = Mitwirkende.objects.create(alt_id=person['id'])
                
            for attr in ['name', 'text_de', 'text_en', 'link', 'level', 
                'start', 'end']:
                if person[attr] == '0000-00-00':
                    person[attr] = '1111-01-01'
                setattr(neu, attr, person[attr])
            
            neu.save()


### ab hier der große Block zum Eintragen der Käufe; dazu werden Nutzer und
### Produkte importiert, dabei die Zuordnung der alten id zu den neuen 
### Instanzen gespeichert, um dann gut Käufe erstellen zu können.

def eintragen_mitglieder(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    mitgliederExt-Tabelle der alten db. Trägt entsprechende Nutzer ein
    und gibt dict alte user_id -> Profil-Instanz zurück """
        
    profil_attributnamen = dict([
        ('stufe', 'Mitgliedschaft'),
        ('anrede', 'Anrede'),
        ('tel', 'Telefon'),
        ('firma', 'Firma'),
        ('strasse', 'Strasse'),
        ('plz', 'PLZ'),
        ('ort', 'Ort'),
        ('land', 'Land'),
        ('guthaben', 'credits_left'),
        ('titel', 'Titel'),
        ('anredename', 'Anredename'),
        ('letzte_zahlung', 'Zahlung'),
        ('datum_ablauf', 'Ablauf'),
        ('alt_id', 'user_id'),
        ('alt_notiz', 'Notiz'),
        ('alt_scholien', 'Scholien'),
        ('alt_mahnstufe', 'Mahnstufe'),
        ('alt_auslaufend', 'auslaufend'),
        ('alt_gave_credits', 'gave_credits'),
        ('alt_registration_ip', 'user_registration_ip')
    ])

    nutzer_attributnamen = dict([
        ('email', 'user_email'),
        ('first_name', 'Vorname'),
        ('last_name', 'Nachname'),
        ('date_joined', 'user_registration_datetime'),
        ('last_login', 'last_login_time'),
    ])
    
    letzte_id = max(Nutzer.objects.all().values_list('id', flat=True))
    
    liste_nutzer = [] # hat dann gleiche Reihenfolge wie daten

    with transaction.atomic():
        for i, zeile in enumerate(daten):
            try:
                if not zeile['user_email']: # das gibt Konflikt mit django-guardians AnonymousUser, der hat auch leere Mail
                    raise Nutzer.DoesNotExist
                nutzer = Nutzer.objects.get(email=zeile['user_email'])
                print("Nutzer gab's schon: %s" % zeile['user_email'])
            except Nutzer.DoesNotExist:
                nutzer = Nutzer.leeren_anlegen() # legt Nutzer mit Profil
                # und Signup-Objekt an; mit Zufalls-Name und -Passwort
                print('Neuer Nutzer mit {}, alte id {} vom {}'.format(
                    zeile['user_email'], 
                    zeile['user_id'], 
                    zeile['user_registration_datetime']))
            nutzer.is_active = True
            nutzer.save()
            liste_nutzer.append(nutzer)
    
    for zeile in daten: # falls None drin steht, gäbe es sonst Fehler
        zeile['Vorname'] = zeile['Vorname'] or ''
        zeile['Nachname'] = zeile['Nachname'] or ''
        for k, v in zeile.items():
            if v == '0000-00-00 00:00:00':
                zeile[k] = '1111-01-01 00:00:00'
            if v == '0000-00-00':
                zeile[k] = '1111-01-01'
        
    def eintragen_nutzer(nutzer, zeile):
        for neu, alt in nutzer_attributnamen.items():
            setattr(nutzer, neu, zeile[alt])

    def eintragen_profil(profil, zeile):
        for neu, alt in profil_attributnamen.items():
            setattr(profil, neu, zeile[alt])
    
    id_zu_profil = {}
    
    with transaction.atomic():
        for i, nutzer in enumerate(liste_nutzer):
            zeile = daten[i]
            eintragen_nutzer(nutzer, zeile)
            pw_alt = zeile['user_password_hash']
            nutzer.password = 'bcrypt$$2b$10${}'.format(pw_alt.split('$')[-1])
            nutzer.save()
            profil = nutzer.my_profile
            eintragen_profil(profil, zeile)
            profil.save()
            id_zu_profil[zeile['user_id']] = profil
    
    return liste_nutzer, id_zu_profil

def eintragen_veranstaltungen(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Veranstaltungen ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_art = { # sucht pks der Arten der Veranstaltungen
        a.bezeichnung: a.pk for a in ArtDerVeranstaltung.objects.all()}
    
    art_von_type = {
        'salon': id_art['Salon'], 
        'media-vortrag': id_art['Vortrag'], 
        'media-salon': id_art['Salon'],
        'media-vorlesung': id_art['Vorlesung'],
        'seminar': id_art['Seminar'],
    }
    
    id_zu_objekt = {}

    with transaction.atomic():
        for zeile in daten:
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
                art_veranstaltung_id=art_von_type[zeile['type']],
                datum=datum, 
                link=zeile['livestream'])
            if zeile['livestream']: 
                v.ob_livestream = True
                v.save()
            id_zu_objekt[zeile['n']] = v
    
    return id_zu_objekt

def eintragen_studiendinger(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Studiendinger ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}

    with transaction.atomic():
        for i, zeile in enumerate(daten):
            if zeile['type'] == 'programm':
                dings = Studiumdings.objects.create(
                    bezeichnung=zeile['title'],
                    slug=zeile['id'],
                    beschreibung1=zeile['text'],
                    beschreibung2=zeile['text2'],
                    preis_teilnahme=zeile['price'],
                    reihenfolge=10*i,)
            if zeile['type'] == 'vortrag':
                dings = Studiumdings.objects.create(
                    bezeichnung=zeile['title'],
                    slug=zeile['id'],
                    beschreibung1=zeile['text'],
                    beschreibung2='Feld nicht genutzt',
                    preis_teilnahme=zeile['price'],
                    reihenfolge=0,)
            
            id_zu_objekt[zeile['n']] = dings

    return id_zu_objekt

def eintragen_buechlein(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Buechlein ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}
    
    with transaction.atomic():
        for zeile in daten:
            buch = Buechlein.objects.create(
                bezeichnung=zeile['title'],
                beschreibung=zeile['text'],
                anzahl_druck=3,
                alte_nr=zeile['n'], 
                slug=zeile['id'])
            
            id_zu_objekt[zeile['n']] = buch
    
    return id_zu_objekt

def eintragen_antiquariat(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Buechlein ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}

    with transaction.atomic():
        for zeile in daten:
            if zeile['format'] == '0001':
                buch = Altes_Buch.objects.create(
                    bezeichnung=zeile['id'],
                    autor_und_titel=zeile['title'],
                    preis_kaufen=zeile['price_book'],
                    slug=zeile['id'], 
                    anzahl_kaufen=zeile['spots'],)
            else:
                print("da gibt's ein 'antiquariat' mit digitalen Formaten!")
            id_zu_objekt[zeile['n']] = buch
    return id_zu_objekt

def eintragen_kaeufe(kliste, id_zu_objekt, id_zu_profil):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    registration-Tabelle der alten db. Außerdem ein mapping der produkt_id 
    der alten db zu model-Instanzen der neuen. Trägt entsprechende Käufe ein
    und gibt dict produkt_id -> model-Instanz zurück """

    with transaction.atomic():
        pass

def kaeufe_aus_db():
    """
    Liest Käufe aus der Datenbank im Parent-Ordner
    
    Idee: öffne Datenbank und hole Zeilen als dict Attribut -> Wert
    erstelle Funktionen, um der id den Nutzer und das Produkt zuzuweisen 
    erstelle Käufe aus Nutzer und Produkt
    
    Idee: man könnte gleich vorher alle Produkte einlesen und in ein dict
    id -> objekt schreiben
    """
    con = lite.connect(os.path.join(BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM mitgliederExt")
        mitglieder = [dict(zeile) for zeile in cur.fetchall()]
        cur.execute("SELECT * FROM produkte")
        produkte = [dict(zeile) for zeile in cur.fetchall()]
        cur.execute("SELECT * FROM registration")
        kaeufe = [dict(zeile) for zeile in cur.fetchall()]
    
    id_zu_objekt = {}
    
    Altes_Buch.objects.all().delete()
    id_zu_objekt.update(eintragen_antiquariat(
        [p for p in produkte if p['type']=='antiquariat']))
    
    print('Antiquariat eingelesen')
    
    Buechlein.objects.all().delete()
    id_zu_objekt.update(eintragen_buechlein(
        [p for p in produkte if p['type']=='scholie']))

    print('Buechlein eingelesen')

    Studiumdings.objects.all().delete()
    id_zu_objekt.update(eintragen_studiendinger(
        [p for p in produkte if p['type'] in 
        ['programm', 'vortrag']]))

    print('Studiumdinger eingelesen')

    Veranstaltung.objects.all().delete()
    id_zu_objekt.update(eintragen_veranstaltungen(
        [p for p in produkte if p['type'] in 
        ['salon', 'media-salon', 'seminar', 'media-vortrag', 
        'media-vorlesung']]))

    print('Veranstaltungen eingelesen')

    print('Nutzer geloescht')
    
    liste_nutzer, id_zu_profil = eintragen_mitglieder(mitglieder)
    try:
        liste_nutzer.append(Nutzer.objects.get(username="admin"))
    except Nutzer.DoesNotExist:
        pass
    try:
        liste_nutzer.append(Nutzer.objects.get(username="AnonymousUser"))
    except Nutzer.DoesNotExist:
        pass
    with transaction.atomic():
        for nutzer in Nutzer.objects.all():
            if nutzer not in liste_nutzer:
                nutzer.delete()
        
    print('Nutzer neu eingelesen, alte gelöscht')
    
    ids_gueltig = id_zu_objekt.keys() # nicht alle wurden eingelesen
    ids_nutzer = id_zu_profil.keys() # anscheinend in alter db gelöscht
    kliste = [k for k in kaeufe if k['event_id'] in ids_gueltig and k['user_id'] in ids_nutzer] 

    print('Gueltige Kaeufe gefunden, beginne Sicherheitspruefung')
    
    for k in kliste:
        if k['user_id'] not in id_zu_profil.keys():
            print('oh, nein! zu user_id %s im Kauf %s gibt es kein Profil!' % (k['user_id'], k['reg_id']))
        if k['event_id'] not in id_zu_objekt.keys():
            print('oh, nein! zu event_id %s im Kauf %s gibt es kein Objekt!' % (k['event_id'], k['reg_id']))
    
    print('Pruefung abgeschlossen.')
    
    pdb.set_trace()        


    
    m_nr = {m['user_id']: i for i, m in enumerate(mitglieder)}
    p_nr = {p['n']: i for i, p in enumerate(produkte)}
    # produkt: gucke nach type; 
    # antiquariat: produkt.id = Altes_Buch.bezeichnung
    # scholie; scholie.titel = Buechlein.bezeichnung; formate: 'Kindle', 'PDF', 'ePub', 'Druck'
    # buch, video, analyse, programm, privatseminar, projekt; fehlt noch das model, oder?
    # salon; salon.id = Veranstaltung.slug; {'vorOrt': 'teilnahme', 'Stream': 'livestream'}
    # seminar; seminar.id = Veranstaltung.slug; {'vorOrt': 'teilnahme', 'Stream': 'livestream'} 
    # media-salon; media-salon.id = Veranstaltung.slug; art=aufzeichnung
    # media-vortrag; id=slug; art '' immer aufzeichnung -> (beim Import alle entsprechend aktivieren)
    # media-vorlesung; genau gleich
    # vortrag - noch importieren
    # ist spots - spots_sold verfügbar, oder spots? ersteres ist (selten) negativ

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

