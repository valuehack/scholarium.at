from django.conf.urls import url

from . import views, models
from Grundgeruest.views import ListeMitMenue, DetailMitMenue, TemplateMitMenue
from Bibliothek.views import liste_buecher

app_name = 'Bibliothek'

urlpatterns = [
    url(r'^$', liste_buecher, name='liste_alle'),
    url(r'^(?P<slug>[\w-]+)$', 
        DetailMitMenue.as_view(
            template_name='Bibliothek/detail_buch.html',
            model=models.Buch,
            context_object_name='buch',
        ), 
        name='detail_buch'),        
    url('^aus_datei_einlesen/([\w-]*)$', views.aus_datei_einlesen, name='einlesen'),
    url('^aus_datei_einlesen$', views.aus_datei_einlesen, name='einlesen'),
    ]

