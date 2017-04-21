from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from .models import *
from Grundgeruest.views import ListeMitMenue, DetailMitMenue


class ListeAlle(ListeMitMenue):
    """ Stellt Liste aller Veranstaltungen dar
    """
    template_name = 'Veranstaltungen/liste_alle.html'
    context_object_name = 'veranstaltungen'
    paginate_by = 2
    model = Veranstaltung    
            
class ListeArt(ListeAlle):
    """ Stellt Liste der Seminare oder Salons dar
    """
    template_name = 'Veranstaltungen/liste_art.html'
    paginate_by = 2
    def get_queryset(self, **kwargs):
        art_name = self.kwargs['art']
        art = get_object_or_404(ArtDerVeranstaltung, bezeichnung=art_name)
        return Veranstaltung.objects.filter(
            art_veranstaltung=art)

def eine_veranstaltung(request, slug):
    if request.user.is_authenticated():
        return DetailMitMenue.as_view(
            template_name='Veranstaltungen/detail.html',
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

