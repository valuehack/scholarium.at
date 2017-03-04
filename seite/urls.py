""" URL Configuration der scholarium-Seite

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from Grundgeruest.views import TemplateMitMenue
from Veranstaltungen.urls import *
import datetime
print(datetime.__file__)

urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^fragen/', 
        TemplateMitMenue.as_view(
            template_name='Gast/fragen.html'), 
        name='gast_fragen'),
    url(r'^scholien/', 
        TemplateMitMenue.as_view(
            template_name='Gast/scholien.html'), 
        name='gast_scholien'),
    url(r'^vortrag/', 
        TemplateMitMenue.as_view(
            template_name='Gast/vortrag.html'), 
        name='gast_vortrag'),
    url(r'^accounts/', include('userena.urls')),
    url(r'^warenkorb/', include('Produkte.urls')),
    url(r'^veranstaltungen/', include(veranstaltungen_urls)),
    url(r'^salon/', include(salons_urls)),
    url(r'^seminare/', include(seminare_urls)),
#    url(r'^bibliothek/', include('Bibliothek.urls')),
#    url(r'^scholien/', include('Scholien.urls')),
    url(r'^', include('Grundgeruest.urls')),
]

