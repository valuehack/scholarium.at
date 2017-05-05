from django.contrib import admin

from .models import Produkt, Spendenstufe, Kauf

admin.site.register(Produkt)
admin.site.register(Spendenstufe)
admin.site.register(Kauf)
