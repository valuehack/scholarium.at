from django.conf.urls import url

from . import models, views
from Grundgeruest.views import DetailMitMenue, ListeMitMenue
from .views import *

app_name = 'Scholien'

urlpatterns = [
    url(r'^$', scholien_startseite, name='index'), 
    url(r'^(?P<slug>[-\w]+)/$', ein_artikel, name='scholie_detail'),
    url(r'^aus_datei_einlesen$', 
        views.aus_datei_einlesen, 
        name='aus_datei_einlesen'), 
    ]
    
