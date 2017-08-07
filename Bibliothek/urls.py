from django.conf.urls import url

from . import views, models
from Grundgeruest.views import ListeMitMenue, DetailMitMenue, TemplateMitMenue

app_name = 'Bibliothek'

urlpatterns = [
    url(r'^$', 
        ListeMitMenue.as_view(
            template_name='Bibliothek/alte_buecher.html',
            model=models.Altes_Buch,
            context_object_name='buecher',
        ), 
        name='alte_liste_buecher'),
    url(r'^$', 
        ListeMitMenue.as_view(
            template_name='Bibliothek/liste_alle.html',
            model=models.Buch,
            paginate_by=300,
            context_object_name='buecher',
        ), 
        name='liste_alle'),
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

