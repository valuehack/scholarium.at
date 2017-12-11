"""
Die Modelle der Scholien-Artikel und Büchlein
"""

from django.db import models
from django.core.files import File
from urllib.request import urlopen
import os, io
from django.urls import reverse
from django.shortcuts import get_object_or_404

from seite.models import Grundklasse
from Produkte.models import KlasseMitProdukten
from Workflow.utils import markdown_to_html


class Artikel(Grundklasse):
    inhalt = models.TextField()
    inhalt_nur_fuer_angemeldet = models.TextField(null=True, blank=True)
    datum_publizieren = models.DateField(null=True, blank=True)
    prioritaet = models.PositiveSmallIntegerField(default=0)
    class Meta:
        verbose_name_plural = "Artikel"
        verbose_name = "Artikel"
        ordering = ['-datum_publizieren']

class MarkdownArtikel(Grundklasse):
    text = models.TextField()
    prioritaet = models.PositiveSmallIntegerField(default=0)
    artikel = models.OneToOneField(Artikel, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Markdown Artikel"
        verbose_name = "Markdown Artikel"
        ordering = ['-zeit_erstellt']
    
    def artikel_erstellen(self):
        inhalt, inhalt_angemeldet = markdown_to_html(self.text)
        if self.artikel: 
            art = self.artikel
            art.slug = self.slug
            art.bezeichnung = self.bezeichnung    
            art.inhalt = inhalt
            art.inhalt_nur_fuer_angemeldet = inhalt_angemeldet
            art.prioritaet = self.prioritaet
        elif Artikel.objects.filter(slug=self.slug).exists():
            raise ValidationError('Artikel-slug existiert bereits.')
        else:
            art = Artikel.objects.create(slug=self.slug, bezeichnung=self.bezeichnung, inhalt=inhalt, inhalt_nur_fuer_angemeldet=inhalt_angemeldet, prioritaet=self.prioritaet)
            self.artikel = art
        art.save()
        print('%s erfolgreich gespeichert.' % self.bezeichnung)
            

    def save(self, *args, **kwargs):
        self.artikel_erstellen()
        super().save(*args, **kwargs)
        

class Buechlein(KlasseMitProdukten):
    pdf = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    epub = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    mobi = models.FileField(upload_to='scholienbuechlein', null=True, blank=True)
    bild = models.ImageField(upload_to='scholienbuechlein', null=True, blank=True)
    beschreibung = models.TextField(max_length=2000, null=True, blank=True)
    alte_nr = models.SmallIntegerField(null=True, editable=False)
    arten_liste = ['druck', 'pdf', 'epub', 'mobi']

    def get_absolute_url(self):
        return reverse('Scholien:buechlein_detail', kwargs={'slug': self.slug})

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
        verbose_name = "Büchlein"
        ordering = ['-alte_nr']
