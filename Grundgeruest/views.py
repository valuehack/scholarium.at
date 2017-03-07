# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from userena.models import UserenaSignup
from django.views.generic import ListView, DetailView, TemplateView
from .models import *

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
    pass

class ListeMitMenue(MenueMixin, ListView):
    pass

class DetailMitMenue(MenueMixin, DetailView):
    pass
        
def index(request):
    liste_menue = erstelle_liste_menue(request.user)
    
    return render(
        request, 
        'base.html', 
        {'liste_menue': liste_menue})
    
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
    f = open('../dumpme', 'r')
    text = f.read()[:-11]
    f.close()
    
    zeilen_def = text.splitlines()[3:42]
    nr_feld = dict([(z.split('`')[1], i) for i, z in enumerate(zeilen_def)])
    
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
    
    def eintragen(objekt, attribut, felder):
        def clean_wert(wert):
            if wert == '0000-00-00 00:00:00':
                return '1900-01-01 00:00:00'
            else:
                return wert
                
        if attribut in nutzer_attributnamen:
            wert = clean_wert(felder[nr_feld[nutzer_attributnamen[attribut]]])
            setattr(objekt, attribut, wert)
        elif attribut in profil_attributnamen:
            wert = clean_wert(felder[nr_feld[profil_attributnamen[attribut]]])
            setattr(objekt, attribut, wert)
            
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

