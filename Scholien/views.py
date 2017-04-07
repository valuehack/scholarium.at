from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from Grundgeruest.views import DetailMitMenue, ListeMitMenue, TemplateMitMenue
from . import models

import pdb

# Create your views here.

def scholien_startseite(request):
    if request.user.is_authenticated():
        return ListeMitMenue.as_view(
            model=models.Artikel,
            template_name='Scholien/liste_artikel.html',
            context_object_name='liste_artikel',
            paginate_by = 5)(request)
    else:
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien.html', 
            )(request) 

@login_required
def ein_artikel(request, slug):
    if request.user.my_profile.darf_scholien_sehen():
        #pdb.set_trace()
        return DetailMitMenue.as_view(
            template_name='Scholien/detail.html',
            model=models.Artikel,
            context_object_name = 'scholie')(request, slug=slug)

def aus_datei_einlesen(request):
    f = open('../dumpscholien', 'r')
    text = f.read()[:-11]
    f.close()
    
    liste_scholien = text.split(');\nINSERT INTO "blog" VALUES(')[1:]
    for scholie_roh in liste_scholien:
        scholie = scholie_roh.split("'")[1::2]
        print(11*'\n'+scholie_roh+11*'\n')
        models.Artikel.objects.create(
            bezeichnung=scholie[1],
            inhalt=scholie[2],
            inhalt_nur_fuer_angemeldet=scholie[3],
            datum_publizieren=scholie[4])
            
    return HttpResponseRedirect('/scholien/')

