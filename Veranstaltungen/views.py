from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from datetime import date

from .models import *
from Grundgeruest.views import ListeMitMenue, DetailMitMenue, TemplateMitMenue


class ListeAlle(ListeMitMenue):
    """ Stellt Liste aller Veranstaltungen dar
    """
    template_name = 'Veranstaltungen/liste_veranstaltungen.html'
    context_object_name = 'veranstaltungen'
    paginate_by = 3
    model = Veranstaltung

def liste_veranstaltungen(request, art):
    if request.user.is_authenticated():
        template_name = 'Veranstaltungen/liste_veranstaltungen.html'
    else:
        template_name = 'Veranstaltungen/liste_veranstaltungen_gast.html'
    
    return ListeArt.as_view(
        template_name=template_name,
        art=art)(request)
    
class ListeArt(ListeAlle):
    """ Klasse zur Darstellung der Seminare oder Salons
    Bekommt als kwargs art übergeben und ob user.is_authenticated()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.art_model = get_object_or_404(
            ArtDerVeranstaltung, bezeichnung=self.art)
        veranstaltungen = Veranstaltung.objects.filter(
            datum__gte=date.today()).filter(
            art_veranstaltung=self.art_model).order_by('datum')
        self.extra_context = {
            'veranstaltungen': veranstaltungen, 
            'art_veranstaltung': self.art_model}
    
    art = 'Salon'
    context_object_name = 'medien'
    paginate_by = 3
    def get_queryset(self, **kwargs):
        medien = [medium for medium in Medium.objects.all()
            if medium.gehoert_zu.art_veranstaltung==self.art_model
            and medium.gehoert_zu.datum <= date.today()]
        medien.sort(key = lambda m: m.datum, reverse=True)
        return medien

class VeranstaltungDetail(DetailMitMenue):
    template_name = 'Veranstaltungen/detail_veranstaltung.html'
    context_object_name = 'veranstaltung'
    def get_object(self, **kwargs):
        art_name = self.kwargs['art']
        slug = self.kwargs['slug']
        art = get_object_or_404(ArtDerVeranstaltung, bezeichnung=art_name)
        return Veranstaltung.objects.filter(
            art_veranstaltung=art).get(slug=slug)
        
        
def eine_veranstaltung(request, slug):
    # gedoppelter code, aber die url /veranstaltungen/... wird eh bald obsolet?
    if request.user.is_authenticated():
        return DetailMitMenue.as_view(
            template_name='Veranstaltungen/detail_veranstaltung.html',
            model=Veranstaltung,
            context_object_name = 'veranstaltung')(request, slug=slug)
    else:
        return HttpResponse('die uneingeloggte Ansicht bitte noch in Veranstaltungen.views implementieren')


def studiumdings_detail(request, slug):
    if request.user.is_authenticated() and request.user.hat_guthaben():
        template_name='Veranstaltungen/detail_studiendings.html'
    else:
        template_name='Veranstaltungen/detail_studiendings_gast.html'
    
    return DetailMitMenue.as_view(
            template_name=template_name,
            model=Studiumdings,
            context_object_name = 'studiumdings')(request, slug=slug)

def vortrag(request):
    if request.user.is_authenticated():
        vortrag = get_object_or_404(Studiumdings, bezeichnung='Vortrag')
        extra_context = {'vortrag': vortrag}
    else:
        extra_context = {}
    return TemplateMitMenue.as_view(
        template_name='Gast/vortrag.html', 
        extra_context=extra_context)(request)

    
def daten_einlesen(request):
    """ wird von url aufgerufen und ruft standalone-Fkt auf """
    aus_alter_db_einlesen()
    return HttpResponseRedirect('/veranstaltungen')
    

def aus_alter_db_einlesen():
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
