from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages

from .models import *
from Produkte.models import Kauf
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
        art=art)(request, page=request.GET.get('seite'))
    
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
            'art_veranstaltung': self.art_model,
            'url_hier': {'Seminar': '/seminare', 'Salon': '/salons'}[self.art],
        }
    
    art = 'Salon'
    context_object_name = 'medien'
    paginate_by = 3
    def get_queryset(self, **kwargs):
        mit_medien = [v for v in Veranstaltung.objects.all()
            if v.art_veranstaltung==self.art_model
            and v.ist_vergangen()
            and v.hat_medien()]
        mit_medien.sort(key = lambda m: m.datum, reverse=True)
        return mit_medien

class VeranstaltungDetail(DetailMitMenue):
    template_name = 'Veranstaltungen/detail_veranstaltung.html'
    context_object_name = 'veranstaltung'
    def get_object(self, **kwargs):        
        art_name = self.kwargs['art']
        slug = self.kwargs['slug']
        
        # das in der Funktion weil Zugriff aus self, eig. Missbrauch
        self.url_hier = '/%s/%s' % (art_name.lower(), slug)
        
        # bestimmt die Instanz für den detail-view
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
            url_hier='/studium/%s/' % slug,
            context_object_name = 'studiumdings')(request, slug=slug)

def vortrag(request):
    vortrag = get_object_or_404(Studiumdings, bezeichnung='Vortrag')
    if request.user.is_authenticated():
        arten_wahl = [
            get_object_or_404(ArtDerVeranstaltung, bezeichnung='Vortrag'),
            get_object_or_404(ArtDerVeranstaltung, bezeichnung='Vorlesung')
        ]
        medien = [v for v in Veranstaltung.objects.all() if
            v.art_veranstaltung in arten_wahl
            and v.hat_medien()]
        extra_context = {'vortrag': vortrag, 'medien': medien}
    else:
        extra_context = { 'vortrag': vortrag, 'url_hier': '/vortrag/'}
    return TemplateMitMenue.as_view(
        template_name='Veranstaltungen/vortrag.html', 
        extra_context=extra_context)(request)


def livestream(request):
    """ soll das nächste salon-Objekt ans livestream-Template geben, falls 
    Termin nah genug und link aktiviert. Sonst später Extraseite, erstmal 
    Link auf nächsten Salon und message, dass zu lange hin """
    
    artsalon = ArtDerVeranstaltung.objects.filter(bezeichnung='Salon')
    
    try:
        salon = Veranstaltung.objects.filter(
            datum__gte=date.today()).filter(
            art_veranstaltung=artsalon).order_by('datum')[0]
    except IndexError:
        messages.warning(request, ('Momentan sind die nächsten Salons noch nicht eingetragen.'))
        return HttpResponseRedirect("/salons/")
    
    from Produkte.templatetags import produkttags
    if not produkttags.ob_livestream_zeigen(salon, request.user.my_profile):
        messages.warning(request, ('Zum nächsten Salon gibt es noch keinen Livestream!'))
    
    return HttpResponseRedirect("/salon/" + salon.slug)


from Grundgeruest.daten_einlesen import veranstaltungen_aus_db
def daten_einlesen(request):
    """ wird von url aufgerufen und ruft standalone-Fkt auf """
    aus_alter_db_einlesen()
    return HttpResponseRedirect('/veranstaltungen')
    


