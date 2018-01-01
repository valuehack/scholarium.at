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
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from Grundgeruest.views import TemplateMitMenue, ListeMitMenue, db_runterladen, zahlen, ListeAktiveMitwirkende
from Grundgeruest.models import Mitwirkende
import Grundgeruest.userena_urls as userena_urls
from Veranstaltungen.urls import *
from Veranstaltungen.models import Studiumdings
from Veranstaltungen.views import studiumdings_detail, vortrag
from Produkte.models import Spendenstufe

urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^fragen/',
        TemplateMitMenue.as_view(
            template_name='Gast/fragen.html'),
        name='gast_fragen'),
    # url(r'^mitwirkende/',
    #     ListeAktiveMitwirkende.as_view(),
    #     name='gast_mitwirkende'),
    url(r'^studium/$',
        ListeMitMenue.as_view(
            model=Studiumdings, # Achtung, es werden nur die studiendinger mit reihenfolge<>0 angezeigt, darüber auskommentieren!
    	    template_name='Veranstaltungen/liste_studien.html',
            url_hier='/studium/',
	        context_object_name = 'studien',
        ),
        name='liste_studium'),
    url(r'^studium/(?P<slug>[-\w]+)/$',
        studiumdings_detail,
        name='studium_detail'),
    url(r'^vortrag/(?P<slug>[-\w]+)/', vortrag, name='vortrag_detail'),
    url(r'^vortrag/', vortrag, name='vortrag'),
    url(r'^nutzer/', include(userena_urls)),
    url(r'^warenkorb/', include('Produkte.urls')),
    url(r'^veranstaltungen/', include(
        veranstaltungen_urls,
        namespace='Veranstaltungen')),
    url(r'^salon', include(
        salons_urls,
        namespace='Veranstaltungen')),
    url(r'^seminar', include(
        seminare_urls,
        namespace='Veranstaltungen')),
    url(r'^buecher/', include('Bibliothek.urls')),
    url(r'^scholien', include('Scholien.urls')),
    url(r'^spende/zahlung', zahlen, name='gast_zahlung'),
    url(r'^spende',
        ListeMitMenue.as_view(
            template_name='Produkte/spende.html',
            model=Spendenstufe,
            context_object_name = 'stufen'),
        name='gast_spende'),
    url(r'^projekte',
        TemplateMitMenue.as_view(
            template_name='Grundgeruest/projekte.html'),
        name='projekte'),
    url(r'^eltern/',
        TemplateMitMenue.as_view(
            template_name='Gast/eltern.html'),
        name='gast_eltern'),
    url(r'^en/',
        TemplateMitMenue.as_view(
            template_name='Gast/englisch.html'),
        name='gast_englisch'),
    url(r'^geheim_db$',
        db_runterladen,
        name='bitte_bald_loeschen'),
    url(r'^nimda/', include('Workflow.urls')),
    url(r'^', include('Grundgeruest.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
