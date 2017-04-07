"""
Die Modelle der Scholien-Artikel und Büchlein
"""

from django.db import models
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
    pdf = models.FileField(upload_to='scholienbuechlein', null=True)
    bild = models.ImageField(upload_to='scholienbuechlein', null=True)
    beschreibung = models.TextField(max_length=2000, null=True, blank=True)
    
    def get_preis(self):
        return 5
    
    class Meta:
        verbose_name_plural = "Büchlein"

