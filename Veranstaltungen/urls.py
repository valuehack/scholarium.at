from django.conf.urls import url

from . import views
from Grundgeruest.views import DetailMitMenue
from .models import Veranstaltung

app_name = 'Veranstaltungen'

veranstaltungen_urls = ([
    url(r'^$', 
        views.ListeAlle.as_view(), 
        name='liste_alle'),
    url(r'^(?P<slug>[-\w]+)/$', 
        views.eine_veranstaltung, 
        name='veranstaltung_detail'),
    url(r'^aus_alt_einlesen', 
        views.daten_einlesen, 
        name='aus_alt_einlesen'),
    ], 'Veranstaltungen')

salons_urls = ([
    url(r'^s/', 
        views.liste_veranstaltungen, 
        {'art': 'Salon'}, name='liste_salons'),
    url(r'^/livestream/', 
        views.livestream, 
        name='aktueller_livestream'),
    url(r'^/(?P<slug>[-\w]+)/$', 
        views.VeranstaltungDetail.as_view(), 
        {'art': 'Salon'}, name='salon_detail'),
    ], 'Veranstaltungen')

seminare_urls = ([
    url(r'^e', 
        views.liste_veranstaltungen, 
        {'art': 'Seminar'}, name='liste_seminare'),
    url(r'^/(?P<slug>[-\w]+)/$', 
        views.VeranstaltungDetail.as_view(), 
        {'art': 'Seminar'}, name='seminar_detail'),
    ], 'Veranstaltungen')
