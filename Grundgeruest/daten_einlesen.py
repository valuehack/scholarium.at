import os, shutil, json
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein
from Bibliothek.models import Buch
from Veranstaltungen.models import Veranstaltung, ArtDerVeranstaltung, Studiumdings
from Produkte.models import Kauf

from django.db import transaction
import sqlite3 as lite

import ipdb

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
    import os 
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

    print('Nutzerattribute und Profilattribute eingetragen')
    
    return liste_nutzer, id_zu_profil

def eintragen_veranstaltungen(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Veranstaltungen ein
    und gibt dict produkt_id -> model-Instanz zurück """
    
    liste_eingetragen = []
    
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
                link=zeile['livestream'],
                anzahl_teilnahme=zeile['spots'])
            if zeile['livestream']: 
                v.ob_livestream = True
                v.save()
            id_zu_objekt[zeile['n']] = (v, zeile['type'])
            liste_eingetragen.append(v)
    
    return id_zu_objekt, liste_eingetragen

def eintragen_studiendinger(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Studiendinger ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}
    liste_eingetragen = []

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
            
            id_zu_objekt[zeile['n']] = (dings, zeile['type'])
            liste_eingetragen.append(dings)

    return id_zu_objekt, liste_eingetragen

def eintragen_buechlein(daten):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Buechlein ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}
    liste_eingetragen = []
    
    with transaction.atomic():
        for zeile in daten:
            buch = Buechlein.objects.create(
                bezeichnung=zeile['title'],
                beschreibung=zeile['text'],
                anzahl_druck=3,
                alte_nr=zeile['n'], 
                slug=zeile['id'])
            
            id_zu_objekt[zeile['n']] = (buch, zeile['type'])
            liste_eingetragen.append(buch)
    
    return id_zu_objekt, liste_eingetragen

def eintragen_buecher(daten, analysen):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    produkte-Tabelle der alten db. Trägt entsprechende Buechlein ein
    und gibt dict produkt_id -> model-Instanz zurück """

    id_zu_objekt = {}
    liste_eingetragen = []

    with transaction.atomic():
        for zeile in daten:
            if zeile['type']=='antiquariat' and zeile['format']=='0001':
                buch = Buch.objects.create(
                    bezeichnung=zeile['title'],
                    preis_kaufen=zeile['price_book'],
                    preis_leihen=zeile['price_book'], #?
                    slug=zeile['id'], 
                    alte_nr=zeile['n'],
                    anzahl_kaufen=zeile['spots'],)
            elif zeile['type']=='antiquariat':
                print("da gibt's ein 'antiquariat' mit digitalen Formaten!")
            elif zeile['type']=='buch' and zeile['format']=='1111':
                buch = Buch.objects.create(
                    bezeichnung=zeile['title'][:-6],
                    preis_druck=zeile['price_book'],
                    preis_pdf=zeile['price'], 
                    preis_epub=zeile['price'], 
                    preis_mobi=zeile['price'], 
                    slug=zeile['id'], 
                    alte_nr=zeile['n'],
                    anzahl_druck=zeile['spots'],
                    ob_pdf=True, ob_mobi=True, ob_epub=True)
            elif zeile['type']=='buch' and zeile['format']=='0111': # nur für Alpenphilosophie, fast doppelter code
                buch = Buch.objects.create(
                    bezeichnung=zeile['title'][:-6],
                    preis_druck=zeile['price_book'],
                    preis_epub=zeile['price'], 
                    preis_mobi=zeile['price'], 
                    slug=zeile['id'], 
                    alte_nr=zeile['n'],
                    anzahl_druck=zeile['spots'],
                    ob_mobi=True, ob_epub=True)
            elif zeile['type']=='buch' and zeile['format']=='0001':
                buch = Buch.objects.create(
                    bezeichnung=zeile['title'],
                    preis_druck=zeile['price_book'],
                    slug=zeile['id'], 
                    alte_nr=zeile['n'],
                    anzahl_druck=zeile['spots'],)
                
            id_zu_objekt[zeile['n']] = (buch, zeile['type'])
            liste_eingetragen.append(buch)

    for zeile in analysen: # zu vorhandenen Objekten zuordnen
        for k, v in id_zu_objekt.copy().items():
            if zeile['title'] in v[0].bezeichnung:
                id_zu_objekt[zeile['n']] = v
            
    return id_zu_objekt, liste_eingetragen

def eintragen_kaeufe(kliste, id_zu_objekt, id_zu_profil):
    """ bekommt eine Liste von dicts mit dem Inhalt von je einer Zeile der
    registration-Tabelle der alten db. Außerdem ein mapping der produkt_id 
    der alten db zu model-Instanzen der neuen. Trägt entsprechende Käufe ein
    und gibt dict produkt_id -> model-Instanz zurück 
    
    kompliziert ist die Zuordnung von format zu art; es gibt in der alten
    db folgende formate der Käufe abhängig vom type vom produkt:
    scholie: PDF, Kindle, ePub, Druck
    antiquariat: Druck
    programm: ''
    seminar: '', vorOrt
    salon: '', vorOrt, vor Ort, Stream 
    media-salon: '', Stream
    media-vortrag: ''
    media-vorlesung: '' """
    
    def reg_zu_kauf(kauf):
        """ nimmt eine Zeile der kliste und gibt objekt und art für den 
        zu erstellenden Kauf aus """
        objekt, type_alt = id_zu_objekt[kauf['event_id']]
        if type_alt in ['programm', 'seminar']:
            art = 'teilnahme'
        elif type_alt == 'antiquariat':
            art = 'kaufen'
        elif type_alt in ['scholie', 'buch']:
            art = {'Druck': 'druck', 
                'PDF': 'pdf',
                '': 'spam',  
                'ePub': 'epub', 
                'Kindle': 'mobi'}[kauf['format']]
            if art=='spam':
                if kauf['quantity']==1:
                    art = 'pdf'
                else:
                    art = 'druck'
        elif type_alt[:5] == 'media':
            art = 'aufzeichnung'
        elif type_alt == 'salon':
            art = 'aufzeichnung' # ist falsch, aber zum Wohl des Kunden
        
        return objekt, art

    with transaction.atomic():
        for kauf in kliste:
            if kauf['reg_datetime'][0] == '0':
                datum = '1111-11-11 11:11:11'
            else:
                datum = kauf['reg_datetime']
            if kauf['reg_notes']:
                kommentar = "Alte reg_id %s, notes %s" % (
                    kauf['reg_id'], kauf['reg_notes'])
            else:
                kommentar = "Aus alter DB mit reg_id %s" % kauf['reg_id']
            objekt, art = reg_zu_kauf(kauf)
            kunde = id_zu_profil[kauf['user_id']]
            menge = kauf['quantity']
            neu = Kauf.neuen_anlegen(objekt, art, menge, kunde, kommentar)
            neu.zeit = datum
            neu.save()
            print('Kauf von %s durch %s angelegt' % (objekt, kunde.user))

def izo_load():
    with open('id_zu_objekt.txt', 'r') as f:
        datei = json.load(f)
        id_zu_objekt = {}
        for k, v in datei.items():
            #print("versuche %s, %s zu importieren" % (k, v[0]))
            try:
                id_zu_objekt[int(k)] = (Kauf.obj_aus_pk(v[0]), v[1])
            except:
                print("nicht geklappt bei " + k)
    return id_zu_objekt

def izo_dump(id_zu_objekt):
    with open('id_zu_objekt.txt', 'w') as f:
        datei = {str(k): (Kauf.obj_zu_pk(v[0]), v[1]) for k, v in id_zu_objekt.items()}
        json.dump(datei, f)

def kaeufe_aus_db():
    """
    Liest Käufe aus der Datenbank im Parent-Ordner
    
    Idee: öffne Datenbank und hole Zeilen als dict Attribut -> Wert
    erstelle Funktionen, um der id den Nutzer und das Produkt zuzuweisen 
    erstelle Käufe aus Nutzer und Produkt
    
    Idee: man könnte gleich vorher alle Produkte einlesen und in ein dict
    id -> objekt schreiben
    
    Es gibt im Moment 2597 registrations in der alten db. Einlesen derer 
    mit produkttyp in ['antiquariat', 'scholie', 'programm', 'vortrag',
    'salon', 'media-salon', 'seminar', 'media-vortrag', 'media-vorlesung']
    gibt 1940 Käufe
    Es fehlen: 
    projekt: 55x 
    privatseminar: 2x
    video: 0x
    buch: 405x
    analyse: 48x
    -> Summe 2450???
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

    # es wird id_zu_objekt der schon früher eingelesenen objekte importiert
    try:
        id_zu_objekt = izo_load()
    except FileNotFoundError:
        id_zu_objekt = {}
    
    def loesche_rest(model, liste_aufheben):
        with transaction.atomic():
            for instanz in model.objects.all():
                if instanz not in liste_aufheben:
                    instanz.delete()

    id_zu_buch, liste_aufheben = eintragen_buecher(
        [p for p in produkte if p['type'] in ['antiquariat', 'buch']], 
        [p for p in produkte if p['type'] == 'analyse']) # kriegt 2 Listen

    id_zu_objekt.update(id_zu_buch)
    loesche_rest(Buch, liste_aufheben)
    print('Antiquariat und Buecher eingelesen')
    
    id_zu_buechlein, liste_aufheben = eintragen_buechlein(
        [p for p in produkte if p['type']=='scholie'])

    id_zu_objekt.update(id_zu_buechlein)
    loesche_rest(Buechlein, liste_aufheben)

    print('Buechlein eingelesen')
    
    id_zu_dings, liste_aufheben = eintragen_studiendinger(
        [p for p in produkte if p['type'] in 
        ['programm', 'vortrag']])

    id_zu_objekt.update(id_zu_dings)
    loesche_rest(Studiumdings, liste_aufheben)

    print('Studiumdinger eingelesen')

    id_zu_veranstaltung, liste_aufheben = eintragen_veranstaltungen(
        [p for p in produkte if p['type'] in 
        ['salon', 'media-salon', 'seminar', 'media-vortrag', 
        'media-vorlesung']])

    id_zu_objekt.update(id_zu_veranstaltung)
    loesche_rest(Veranstaltung, liste_aufheben)

    print('Veranstaltungen eingelesen')

    izo_dump(id_zu_objekt)
                
    liste_nutzer, id_zu_profil = eintragen_mitglieder(mitglieder)
    
    print('Nutzer eingelesen, lösche überschüssige')
    
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
        
    print('Alte Nutzer gelöscht')
    
    ids_gueltig = id_zu_objekt.keys() # nicht alle wurden eingelesen
    ids_nutzer = id_zu_profil.keys() # anscheinend in alter db gelöscht
    kliste = [k for k in kaeufe if k['event_id'] in ids_gueltig and k['user_id'] in ids_nutzer] 

    print('Gültige Käufe gefunden, beginne Sicherheitspruefung')
    
    for k in kliste:
        if k['user_id'] not in id_zu_profil.keys():
            print('oh, nein! zu user_id %s im Kauf %s gibt es kein Profil!' % (k['user_id'], k['reg_id']))
        if k['event_id'] not in id_zu_objekt.keys():
            print('oh, nein! zu event_id %s im Kauf %s gibt es kein Objekt!' % (k['event_id'], k['reg_id']))
    
    print('Prüfung abgeschlossen.')
    
    Kauf.objects.all().delete()
    eintragen_kaeufe(kliste, id_zu_objekt, id_zu_profil)

    # video, analyse, programm, privatseminar, projekt; fehlt noch das model, oder?

def mediendateien_einlesen():
    id_zu_objekt = izo_load()
    name_zu_objekt = {v[0].slug: v[0] for k, v in id_zu_objekt.items()}
    objekte_namen = list(name_zu_objekt.keys())
    
    von_ordner = '/home/scholarium/godaddy_daten/down_secure/content_secure/'
    dateinamen = os.listdir(von_ordner)
    
    def datei_zuordnen(objekt, dateiname):
        endung = dateiname.split('.')[-1]
        feldname = endung if endung in ['pdf', 'epub', 'mobi'] else 'datei'
        dateifeld = getattr(objekt, feldname)
        
        if isinstance(objekt, Veranstaltung):
            praefix = 'veranstaltungen/'
        elif isinstance(objekt, Buch):
            praefix = 'buecher/'
        elif isinstance(objekt, Buechlein):
            praefix = 'scholienbuechlein/'
        else: 
            praefix = 'rest/'
        nach_ordner = os.path.join(MEDIA_ROOT, praefix)
        
        ob_feld = 'ob_aufzeichnung' if feldname=='datei' else 'ob_'+feldname
        def anschalten():
            feld = getattr(objekt, ob_feld)
            feld = True
            objekt.save()

        if dateifeld and os.path.isfile(os.path.join(MEDIA_ROOT, dateifeld.name)):
            print("%s hatte schon die Datei %s" % (objekt, dateifeld.name))
            anschalten()
            return

        neuname = '%s_%s.%s' % (objekt.slug, Nutzer.erzeuge_zufall(8, 2), endung)
        shutil.copy2(von_ordner+dateiname, MEDIA_ROOT+praefix+neuname)
        dateifeld.name = praefix + neuname
        anschalten()
                
        
    for name in objekte_namen:
        for dateiname in dateinamen:
            if name == dateiname.split('.')[0]:
                print("%s in %s" % (name, dateiname))
                datei_zuordnen(name_zu_objekt[name], dateiname)

