"""

"""

from django.db import models
from Produkte.models import KlasseMitProdukten

class Buch(KlasseMitProdukten):
    arten_liste = ['kaufen', 'leihen']
    titel = models.CharField(
        max_length=255,
        null=True, blank=True)
    autor = models.CharField(
        max_length=255,
        null=True, blank=True)
    isbn = models.CharField(
        max_length=40,
        null=True, blank=True)
    adresse = models.CharField(
        max_length=100,
        null=True, blank=True)
    ausgabe = models.CharField(
        max_length=100,
        null=True, blank=True)
    herausgeber = models.CharField(
        max_length=100,
        null=True, blank=True)
    serie = models.CharField(
        max_length=100,
        null=True, blank=True)
    notiz = models.CharField(
        max_length=100,
        null=True, blank=True)
    jahr = models.CharField(
        max_length=4,
        null=True, blank=True)
    sprache = models.CharField(
        max_length=3,
        null=True, blank=True)
    exlibris = models.CharField(
        max_length=40,
        null=True, blank=True)
    stichworte = models.CharField(
        max_length=255,
        null=True, blank=True)
    zusammenfassung = models.TextField(
        null=True, blank=True)
    
    def preis_ausgeben(self, art):
        if art=='leihen':
            return self.finde_preis(art) or 13
        elif art=='kaufen':
            return self.finde_preis(art) or 37
    
    class Meta:
        verbose_name_plural = 'Bücher'
