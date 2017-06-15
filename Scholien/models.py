"""
Die Modelle der Scholien-Artikel und Büchlein
"""

from django.db import models
from django.core.files import File
from urllib.request import urlopen
import os, io

from seite.models import Grundklasse
from Produkte.models import KlasseMitProdukten


class Artikel(Grundklasse):
    inhalt = models.TextField()
    inhalt_nur_fuer_angemeldet = models.TextField(null=True, blank=True)
    datum_publizieren = models.DateField(null=True, blank=True)
    class Meta:
        verbose_name_plural = "Artikel"
        ordering = ['-datum_publizieren']

class Buechlein(KlasseMitProdukten):
    pdf = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    epub = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    mobi = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    bild = models.ImageField(upload_to='scholienbuechlein', null=True, blank=True)
    beschreibung = models.TextField(max_length=2000, null=True, blank=True)
    alte_nr = models.SmallIntegerField(null=True, editable=False)
    arten_liste = ['druck', 'pdf', 'epub', 'mobi']
    
    def preis_ausgeben(self, art):
        if self.finde_preis(art):
            return self.finde_preis(art)
        else:
            if art == 'druck':
                return 15
            else: 
                return 5
    
    def bild_holen(self, bild_url, dateiname):
        response = urlopen(bild_url)
        datei_tmp = io.BytesIO(response.read())
        self.bild.save(
            os.path.basename(dateiname),
            File(datei_tmp)
            )
        self.save()
    
    class Meta:
        verbose_name_plural = "Büchlein"
        ordering = ['-alte_nr']
