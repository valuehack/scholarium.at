from django.contrib import admin

from .models import *

class MediumInline(admin.TabularInline):
    model = Medium
    fields = ('datei', 'slug')
    extra = 1

class VeranstaltungAdmin(admin.ModelAdmin):
    inlines = [MediumInline]

admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(ArtDerVeranstaltung)
admin.site.register(Medium)
admin.site.register(Studiumdings)
