from django.contrib import admin

from .models import Veranstaltung, ArtDerVeranstaltung, Studiumdings

admin.site.register(Veranstaltung)
admin.site.register(ArtDerVeranstaltung)
admin.site.register(Studiumdings)
