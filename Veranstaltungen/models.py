"""
Die Modelle der Veranstaltungen und Medien
 - die ArtDerVeranstaltung speichert gemeinsame Attribute
 - eine Veranstaltung muss einer Art zugeordnet sein (zu überdenken?)
 - ein Medium kann gehoert_zu Veranstaltung sein und erbt div. Attribute
 - kann auch selbst Preis, Datum, etc, festlegen
 - beim 1.Speichern von Veranstaltung oder Medium wird neues Produkt erstellt
"""

from django.db import models
from seite.models import Grundklasse
from Produkte.models import KlasseMitProdukten
from django.core.urlresolvers import reverse
import random, string
    

class Veranstaltung(KlasseMitProdukten):
    beschreibung = models.TextField()
    datum = models.DateField()
    art_veranstaltung = models.ForeignKey('ArtDerVeranstaltung')
    
    arten_liste = ['teilnahme', ]

    class Meta:
        verbose_name_plural = "Veranstaltungen"
    
    def preis_ausgeben(self, art='teilnahme'):
        """ Preis ausgeben, es gibt nur eine art für Präsenz? oder Medium-model hier einfügen, dann mehr? """
        if art not in self.arten_liste:
            raise ValueError('Bitte gültige Art angeben')
        elif self.finde_preis(art):
            return self.finde_preis(art)
        else: # das ändern, falls es mehrere Arten gibt
            return self.art_veranstaltung.preis_praesenz
    
    def get_url(self):
        if self.art_veranstaltung.bezeichnung == 'Salon':
            return '/salon/%s' % self.slug
        elif self.art_veranstaltung.bezeichnung == 'Seminar':
            return '/seminar/%s' % self.slug
    

class Studiumdings(KlasseMitProdukten):
    beschreibung1 = models.TextField()
    beschreibung2 = models.TextField()
    arten_liste = ['teilnahme', ]
    class Meta:
        verbose_name_plural = "Studiendinger"
        

class Medium(KlasseMitProdukten):
    gehoert_zu = models.ForeignKey(Veranstaltung, null=True, blank=True)
    datei = models.FileField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    arten_liste = ['livestream', 'aufzeichnung']
    # folgendes v.a. relevant wenn keine Veranstaltung verknüpft ist:
    typ = models.CharField(max_length=30, null=True, blank=True)
    beschreibung = models.TextField(max_length=2000, null=True, blank=True)
    datum = models.DateField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Medien"
    
    def __str__(self):
        return '{} ({})'.format(self.bezeichnung, self.slug) 
        
    def save(self, *args, **kwargs):
        self.beschreibung = self.beschreibung or self.gehoert_zu.beschreibung
        self.bezeichnung = self.bezeichnung or self.gehoert_zu.bezeichnung
        self.typ = self.typ or self.gehoert_zu.art_veranstaltung.bezeichnung
        self.datum = self.datum or self.gehoert_zu.datum
        if not self.pk:
            self.slug = ''.join(random.sample(string.ascii_lowercase, 12))
        super().save(*args, **kwargs)
        

class ArtDerVeranstaltung(Grundklasse):
    beschreibung = models.TextField(
        max_length=1200, 
        null=True, blank=True)    
    preis_praesenz = models.SmallIntegerField()
    # Achtung, hier Felder einfügen wenn mehr Arten von Medien dazukommen
    preis_livestream = models.SmallIntegerField(null=True, blank=True)
    preis_aufzeichnung = models.SmallIntegerField(null=True, blank=True)

    max_teilnehmer = models.SmallIntegerField(null=True, blank=True)
    zeit_beginn = models.TimeField()
    zeit_ende = models.TimeField()
    class Meta:
        verbose_name_plural = "Arten der Veranstaltungen"
