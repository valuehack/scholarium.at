from django.contrib import admin

from .models import *
from Produkte.models import Produkt

class MediumInline(admin.TabularInline):
    model = Medium
    fields = ('datei', 'slug')
    extra = 1

class ProduktInline(admin.TabularInline):
    model = Produkt
    fields = ('slug', 'preis')
    extra = 1

class VeranstaltungAdmin(admin.ModelAdmin):
    inlines = [MediumInline, ProduktInline]

class MediumAdmin(admin.ModelAdmin):
    inlines = [ProduktInline]

admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(ArtDerVeranstaltung)
admin.site.register(Medium, MediumAdmin)
