from django.conf.urls import url

from . import views, models
from Grundgeruest.views import ListeMitMenue

app_name = 'Bibliothek'

urlpatterns = [
    url(r'^$', 
        ListeMitMenue.as_view(
            template_name='Bibliothek/liste_alle.html',
            model=models.Buch,
            context_object_name='buecher',
        ), 
        name='liste_alle'),
    url('^aus_datei_einlesen/([\w-]*)$', views.aus_datei_einlesen, name='einlesen'),
    url('^aus_datei_einlesen$', views.aus_datei_einlesen, name='einlesen'),
    ]

