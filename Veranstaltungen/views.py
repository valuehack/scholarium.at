from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from datetime import date

from .models import *
from Grundgeruest.views import ListeMitMenue, DetailMitMenue


class ListeAlle(ListeMitMenue):
    """ Stellt Liste aller Veranstaltungen dar
    """
    template_name = 'Veranstaltungen/liste_veranstaltungen.html'
    context_object_name = 'veranstaltungen'
    paginate_by = 3
    model = Veranstaltung
    
class ListeArt(ListeAlle):
    """ Stellt Liste der Seminare oder Salons dar
    """
    template_name = 'Veranstaltungen/liste_veranstaltungen.html'
    veranstaltungen = Veranstaltung.objects.filter(datum__gte=date.today())
    extra_context = {'veranstaltungen': veranstaltungen.order_by('datum')}
    context_object_name = 'medien'
    paginate_by = 3
    def get_queryset(self, **kwargs):
        art_name = self.kwargs['art']
        art = get_object_or_404(ArtDerVeranstaltung, bezeichnung=art_name)
        medien = [medium for medium in Medium.objects.all()
            if medium.gehoert_zu.art_veranstaltung.bezeichnung==art_name
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

def daten_einlesen(request):
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

    Veranstaltung.objects.all().delete()
    Medium.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM produkte WHERE type in ('salon', 'seminar');")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
    
    arten = {'salon': ArtDerVeranstaltung.objects.get(bezeichnung='Salon'),
        'seminar': ArtDerVeranstaltung.objects.get(bezeichnung='Seminar')}
    
    with transaction.atomic():
        for zeile in zeilen:
            v = Veranstaltung.objects.create(
                bezeichnung=zeile['title'],
                slug=zeile['id'],
                beschreibung=zeile['text'],
                art_veranstaltung=arten[zeile['type']],
                datum=zeile['start'].split(' ')[0])
            m = Medium.objects.create(gehoert_zu=v)
            m.link = zeile['livestream']
