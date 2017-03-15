from django.conf.urls import url

from . import views
from Grundgeruest.views import DetailMitMenue
from .models import Veranstaltung

app_name = 'Veranstaltungen'

veranstaltungen_urls = [
    url(r'^$', 
        views.ListeAlle.as_view(), 
        name='liste_alle'),
    url(r'^(?P<slug>[-\w]+)/$', 
        views.eine_veranstaltung, 
        name='veranstaltung_detail'),
    ]

salons_urls = [
    url(r'^$', 
        views.ListeAlle.as_view(), 
        {'art': 'Salon'}, name='liste_salons'),
    ]

seminare_urls = [
    url(r'^$', 
        views.ListeAlle.as_view(), 
        {'art': 'Seminar'}, name='liste_seminare'),
    ]

