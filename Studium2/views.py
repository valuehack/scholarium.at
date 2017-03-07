from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse

from .models import *
from Grundgeruest.views import ListeMitMenue

class ListeAlle(ListeMitMenue):
    """ Stellt Liste aller Studiumsmöglichkeiten dar
    """
    template_name = 'Studium/liste_alle.html'
    context_object_name = 'studien'
    """paginate_by = 2"""
    model = Studium    
            
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
    
