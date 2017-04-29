# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from userena.models import UserenaSignup
from userena.mail import UserenaConfirmationMail
from userena.settings import USERENA_ACTIVATED
from django.views.generic import ListView, DetailView, TemplateView
from userena.utils import generate_sha1
from guardian.models import UserObjectPermission
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.db import transaction
import sqlite3 as lite
import pdb
from .models import *
from Scholien.models import Artikel
from Veranstaltungen.models import Veranstaltung, Medium
from Bibliothek.models import Buch
from .forms import ZahlungFormular

import pdb

def erstelle_liste_menue(user=None):
    if user is None or not user.is_authenticated():
        menue = GanzesMenue.objects.get(bezeichnung='Gast')
    else: # d.h. wenn nicht AnonymousUser zugreift
        return [
            ({'bezeichnung': 'Scholien', 'slug': 'scholien'}, [
            {'bezeichnung': 'Artikel', 'slug': 'scholien'},
            {'bezeichnung': 'Büchlein', 'slug': 'scholienbuechlein'}
            ]),
            ({'bezeichnung': 'Veranstaltungen', 'slug': 'veranstaltungen'}, [
            {'bezeichnung': 'Alle', 'slug': 'veranstaltungen'},
            {'bezeichnung': 'Salon', 'slug': 'salons'},
            {'bezeichnung': 'Seminare', 'slug': 'seminare'},
            {'bezeichnung': 'Vortrag', 'slug': 'vortrag'},
            ]),
            ({'bezeichnung': 'Bücher', 'slug': 'buecher'}, [
            ]),
            ({'bezeichnung': 'Medien', 'slug': 'medien'}, [
            {'bezeichnung': 'Alle', 'slug': 'medien'},
            {'bezeichnung': 'Salon', 'slug': 'media-salon'},
            {'bezeichnung': 'Vorlesung', 'slug': 'media-vorlesung'},
            {'bezeichnung': 'Vortrag', 'slug': 'media-vortrag'},
            ]),
            ({'bezeichnung': 'Studium', 'slug': 'studium'}, [
            {'bezeichnung': 'Studium Generale', 'slug': 'studium'},
            {'bezeichnung': 'craftprobe', 'slug': 'craftprobe'},
            {'bezeichnung': 'Stipendium', 'slug': 'baader-stipendium'},
            {'bezeichnung': 'Beratung', 'slug': 'beratung'},
            ]),
            ({'bezeichnung': 'Projekte', 'slug': 'projekte'}, [
            ]),
        ]
    liste_punkte = []
    for punkt in menue.hauptpunkt_set.all():
        unterpunkte = punkt.unterpunkt_set.all
        liste_punkte.append((punkt, unterpunkte))
    return liste_punkte

class MenueMixin():
    extra_context = {}
    def get_context_data(self, **kwargs):
        liste_menue = erstelle_liste_menue(self.request.user)
        context = super().get_context_data(**kwargs)
        context['liste_menue'] = liste_menue
        context.update(self.extra_context)
        return context        

class TemplateMitMenue(MenueMixin, TemplateView):
    pass 
    
class ListeMitMenue(MenueMixin, ListView):
    pass

class DetailMitMenue(MenueMixin, DetailView):
    pass
        
def index(request):
    if request.user.is_authenticated():
        liste_artikel = Artikel.objects.order_by('-datum_publizieren')[:4]
        veranstaltungen = Veranstaltung.objects.order_by('-datum')[:3]
        medien = Medium.objects.order_by('-zeit_erstellt')[:3]
        buecher = Buch.objects.order_by('-zeit_erstellt')[:3]
        return TemplateMitMenue.as_view(
            template_name='startseite.html',
            extra_context={
                'liste_artikel': liste_artikel, 
                'medien': medien,
                'veranstaltungen': veranstaltungen,
                'buecher': buecher
            })(request)
    else:
        return TemplateMitMenue.as_view(
            template_name='Gast/startseite_gast.html'
            )(request)
    
def zahlen(request):
    # falls POST von unangemeldet, keine Fehlermeldungen:
    #if request.method=='POST' and 'von_spende' in request.POST:
    #    formular = ZahlungFormular(request.POST)
    
    # falls POST von hier, werden Daten verarbeitet:
    if request.method=='POST':
        # eine form erstellen, insb. um sie im Fehlerfall zu nutzen:
        formular = ZahlungFormular(request.POST)
        # und falls alle Eingaben gültig sind, Daten verarbeiten: 
        if formular.is_valid():
            if not (request.user.is_authenticated() or
                Nutzer.objects.filter(email=request.POST['email'])):

                # erstelle neuen Nutzer mit eingegebenen Daten:
                nutzer = Nutzer.neuen_erstellen(request.POST['email'])
                profil = nutzer.my_profile
                signup = nutzer.userena_signup
                nutzer.first_name = request.POST['vorname']
                nutzer.last_name = request.POST['nachname']
                profil.stufe = int(request.POST['stufe'])
                profil.guthaben_aufladen(request.POST['betrag'])
                # ? hier noch Zahlungsdatum eintragen, oden bei Eingang ?
                for attr in ['anrede', 'tel', 'firma', 'strasse', 'plz', 
                    'ort', 'land']:
                    setattr(profil, attr, request.POST[attr])

                nutzer.save()
                profil.save()
            else:
                print('{0}gibts schon{0}'.format(10*'\n'))
                
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')
        
        if 'von_spende' in request.POST:
            formular = ZahlungFormular()
    
    # if a GET (or any other method) we'll create a blank form
    else:
        formular = ZahlungFormular()

    stufe = request.POST.get('stufe', 'Gast')
    betrag = request.POST.get('betrag', '75')

    return render(request, 'Produkte/zahlung.html', 
        {'formular': formular, 'betrag': betrag, 'stufe': stufe})    
        


def seite_rest(request, slug):
    punkte = (Hauptpunkt.objects.filter(slug=slug) or 
              Unterpunkt.objects.filter(slug=slug))
    if not punkte: 
        raise Http404
    liste_menue = erstelle_liste_menue()
    return render(
        request, 
        'Grundgeruest/seite_test.html', 
        {'punkt': punkte[0], 'liste_menue': liste_menue})

def aus_datei_mitglieder_einlesen(request):
    """
    Liest Mitglieder aus der Datenbank im Parent-Ordner
    
    Idee: öffne Datenbank und hole Zeilen als dict Attribut -> Wert
    erstelle dict für alte Attributnamen -> neue Namen 
    erstelle Liste von Nutzern und speichere sie (wegen Profil und Signup)
    füge für jeden Nutzer alle Attribute hinzu, speichere
    """
    con = lite.connect('../alte_db.sqlite3')
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM mitgliederExt")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
            
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
    
    zeilen = zeilen[:]
    Nutzer.objects.filter(id__gt=6).delete()    
        
    letzte_id = max(Nutzer.objects.all().values_list('id', flat=True))
    liste_nutzer = Nutzer.objects.bulk_create(
        [Nutzer(
            username='alteDB_%s' % zeile['user_id'], 
            id=letzte_id+1+i
        ) for i, zeile in enumerate(zeilen)])
        
    for zeile in zeilen: # falls None drin steht, gäbe es sonst Fehler
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
    
    with transaction.atomic():
        for i, nutzer in enumerate(liste_nutzer):
            zeile = zeilen[i]
            eintragen_nutzer(nutzer, zeile)
            pw_alt = zeile['user_password_hash']
            nutzer.password = 'bcrypt$$2b$10${}'.format(pw_alt.split('$')[-1])
            signup = MeinUserenaSignup.objects.get_or_create(user=nutzer)[0]
            signup.activation_key = USERENA_ACTIVATED
            signup.activation_notification_send = True
            profil = ScholariumProfile.objects.create(user=nutzer)
            eintragen_profil(profil, zeile)
            profil.save()
            signup.save()
            nutzer.save()


def alles_aus_mysql_einlesen():
    """ Laedt newBig Datenbank runter und liest Daten ein (aktuelle Zeilen
    werden vorher geloescht) fuer:
     - Scholienartikel
     - Veranstaltungen
     - [zu vervollständigen]
    """
    import os 
    from Veranstaltungen.views import aus_alter_db_einlesen as einlesen_v
    from Scholien.views import aus_alter_db_einlesen as einlesen_s
    liste_dateien = os.listdir('.')
    if not 'alte_db.sql' in liste_dateien:
        print("ich will jetzt die newBig Datenbank runterladen...")
        os.system('mysqldump --extended-insert=FALSE --complete-insert=TRUE -h 37.148.204.116 -u newBig -p newBig > alte_db.sql')
        print('habe newBig nach alte_db.sql runtergeladen')
    if not 'alte_db.sqlite3' in liste_dateien:
        os.system('./mysql2sqlite alte_db.sql | sqlite3 alte_db.sqlite3')
        print('habe alte_db.sqlite3 erzeugt')
    if input('...werde jetzt Veranstaltungen und Medien löschen und aus alter DB übernehmen - richtig? Zum Abbrechen etwas eingeben, Fortfahren mit nur Eingabetaste'):
        print('abgebrochen')
    else:
        einlesen_v()
        print('eingelesen')
    if input('...werde jetzt Scholienartikel löschen und aus alter DB übernehmen - richtig? Zum Abbrechen etwas eingeben, Fortfahren mit nur Eingabetaste'):
        print('abgebrochen')
    else:
        einlesen_s()
        print('eingelesen')


def db_runterladen(request):
    from django.utils.encoding import smart_str
    import os
    from seite.settings import BASE_DIR
     
    with open(os.path.join(BASE_DIR, 'db.sqlite3'), 'rb') as datei:
        datenbank = datei.read()

    response = HttpResponse(datenbank, content_type='application/force-download') 
    response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
    
    return response

