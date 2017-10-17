from django.contrib import admin

import ipdb

# Register your models here.

from .models import *

class ZeileInline(admin.TabularInline):
    model = Zeile
    fields = ('zeit_geaendert', 'autor', 'text')
    readonly_fields = ('zeit_geaendert', 'autor')
    extra = 0  

class ListeAdmin(admin.ModelAdmin):
    inlines = [ZeileInline]

admin.site.register(Liste, ListeAdmin)
admin.site.register(Zeile)

