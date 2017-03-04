from django.conf.urls import url

from . import models, views
from Grundgeruest.views import DetailMitMenue, ListeMitMenue

app_name = 'Scholien'

urlpatterns = [
    url(r'^$', 
        ListeMitMenue.as_view(
            model=models.Artikel,
            template_name='Scholien/liste_artikel.html',
            context_object_name='liste_artikel',
            paginate_by = 5,), 
        name='liste_artikel'),
    url(r'^(?P<slug>[-\w]+)/$', 
        DetailMitMenue.as_view(
            template_name='Scholien/detail.html',
            model=models.Artikel,
            context_object_name = 'scholie'), 
        name='veranstaltung_detail'),
    url(r'^aus_datei_einlesen$', 
        views.aus_datei_einlesen, 
        name='aus_datei_einlesen'), 
    ]
    
