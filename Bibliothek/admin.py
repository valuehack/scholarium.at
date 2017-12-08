from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(Buch)
class BuchAdmin(admin.ModelAdmin):
    list_display = ('autor', 'titel', 'herausgeber', 'bezeichnung')
    list_filter = ['jahr']
    search_fields = ['bezeichnung']
