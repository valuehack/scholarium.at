# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from userena.models import UserenaSignup
from userena.settings import USERENA_ACTIVATED
from django.views.generic import ListView, DetailView, TemplateView
from django.db import transaction
import sqlite3 as lite
import pdb
from .models import *
from Scholien.models import Artikel
from Veranstaltungen.models import Veranstaltung, Medium
from Bibliothek.models import Buch
from .forms import ZahlungFormular

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
            {'bezeichnung': 'Salon', 'slug': 'salon'},
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
    def get_context_data(self, **kwargs):
        liste_menue = erstelle_liste_menue(self.request.user)
        context = super().get_context_data(**kwargs)
        context['liste_menue'] = liste_menue
        return context        

class TemplateMitMenue(MenueMixin, TemplateView):
    extra_context = {}
    def get_context_data(self, **kwargs):
        context = super(TemplateMitMenue, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

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
    # falls POST, werden Daten verarbeitet:
    if request.method == 'POST':
        # eine form erstellen, insb. um sie im Fehlerfall zu nutzen:
        formular = ZahlungFormular(request.POST)
        # und falls alle Eingaben gültig sind, Daten verarbeiten: 
        if formular.is_valid():
            if not (request.user.is_authenticated() or
                Nutzer.objects.filter(email=request.POST['email'])):
                # erstelle neuen Nutzer mit eingegebenen Daten:
                nutzer = Nutzer.objects.create(email=request.POST['email'])
                signup = UserenaSignup.objects.create(user=nutzer)
                profil = ScholariumProfile.objects.create(user=nutzer)
                nutzer.first_name = request.POST['vorname']
                nutzer.last_name = request.POST['nachname']
                for attr in ['anrede', 'tel', 'firma', 'strasse', 'plz', 
                    'ort']:
                    setattr(profil, attr, request.POST[attr])
                nutzer.save()
                profil.save()
                signup.save()
                print('{0}gibts noch nicht{0}'.format(10*'\n'))
            else:
                print('{0}gibts schon{0}'.format(10*'\n'))
                
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        formular = ZahlungFormular()

    return render(request, 'Produkte/zahlung.html', {'formular': formular})    
        


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
    con = lite.connect('../mysqlite3.db')
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
            signup = UserenaSignup.objects.get_or_create(user=nutzer)[0]
            signup.activation_key = USERENA_ACTIVATED
            signup.activation_notification_send = True
            profil = ScholariumProfile.objects.create(user=nutzer)
            eintragen_profil(profil, zeile)
            profil.save()
            signup.save()
            nutzer.save()
    
    pdb.set_trace()
        
    


    liste_user = text.split(');\nINSERT INTO "mitgliederExt" VALUES(')[1:]
    for u in liste_user[2:4]:
        wert = lambda s: felder[nr_feld[profil_attributnamen[s]]]
        felder = [f.strip("'") for f in u.split(",")]
        neuer_nutzer = Nutzer(username='alteDB_%s'%felder[nr_feld['user_id']])
        for attribut in nutzer_attributnamen:
            eintragen(neuer_nutzer, attribut, felder)
        pwalt = felder[nr_feld['user_password_hash']]
        neuer_nutzer.password = 'bcrypt$$2b$10${}'.format(pwalt.split('$')[-1])
        neuer_nutzer.save()
        us = UserenaSignup.objects.get_or_create(user=neuer_nutzer)[0]
        neuer_nutzer.userena_signup = us
        profil = ScholariumProfile.objects.create(user=neuer_nutzer)
        for attribut in profil_attributnamen:
            eintragen(profil, attribut, felder)
        neuer_nutzer.save()
                    
    return HttpResponseRedirect('/accounts/')

def db_runterladen(request):
    from django.utils.encoding import smart_str
    import os
    from seite.settings import BASE_DIR
     
    with open(os.path.join(BASE_DIR, 'db.sqlite3'), 'rb') as datei:
        datenbank = datei.read()

    response = HttpResponse(datenbank, content_type='application/force-download') 
    response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
    
    return response

