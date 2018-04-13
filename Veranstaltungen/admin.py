from django.contrib import admin

from .models import Veranstaltung, ArtDerVeranstaltung, Studiumdings


class VeranstaltungsAdmin(admin.ModelAdmin):
    list_display = ['bezeichnung', 'art_veranstaltung', 'datum']
    list_filter = ['datum', 'art_veranstaltung']
    search_fields = ['bezeichnung']


admin.site.register(Veranstaltung, VeranstaltungsAdmin)
admin.site.register(ArtDerVeranstaltung)
admin.site.register(Studiumdings)
