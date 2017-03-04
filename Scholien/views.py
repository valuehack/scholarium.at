from django.shortcuts import render
from django.http import HttpResponseRedirect
from . import models

# Create your views here.

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

