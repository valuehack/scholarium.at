"""
Die Datenmodelle für Notizzettel:
Zeilen sind verknüpft zu Listen (jede für eine Instanz/url)
"""

from django.db import models
from django.conf import settings
from seite.models import Grundklasse
from Veranstaltungen.models import Veranstaltung

import ipdb


class Liste(Grundklasse):
    """ Attribute einer Liste """
    salon = models.OneToOneField(Veranstaltung)
    bezeichnung = None
    class Meta:
        verbose_name = 'Notizzettel'
        verbose_name_plural = 'Notizzettel'
    
    def __str__(self):
        return 'Liste zu %s' % self.salon

class Zeile(Grundklasse):
    """ Eine konkrete Veranstaltung: Seminar, Wettbewerbsrunde, etc. """
    liste = models.ForeignKey(Liste)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL)
    text = models.CharField(max_length=255)
    zeit_geaendert = models.DateTimeField(
        auto_now=True,
        editable=False)
    bezeichnung = None
    def autor_ausgeben(self):
        return '<a href="/nutzer/%s">%s</a>' % (self.autor.username, self.autor.email)
            
    def __str__(self):
        return 'Notiz in %s von %s' % (self.liste, self.zeit_geaendert)
    
    class Meta: 
        ordering = ["-zeit_erstellt"]
        verbose_name = 'Notizzeile'
        verbose_name_plural = 'Notizzeilen'

