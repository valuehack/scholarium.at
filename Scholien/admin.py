from django.contrib import admin

from .models import Artikel, Buechlein, MarkdownArtikel


class Artikeladmin(admin.ModelAdmin):
    list_display = ['bezeichnung', 'datum_publizieren', 'prioritaet']
    list_filter = ['datum_publizieren', 'prioritaet']
    search_fields = ['bezeichnung']


class MDArtikelAdmin(admin.ModelAdmin):
    list_display = ['bezeichnung', 'prioritaet']
    list_filter = ['prioritaet']
    search_fields = ['bezeichnung']


admin.site.register(Buechlein)
admin.site.register(Artikel, Artikeladmin)
admin.site.register(MarkdownArtikel, MDArtikelAdmin)
