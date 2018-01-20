from django.contrib import admin

from .models import Artikel, Buechlein, MarkdownArtikel

# Register your models here.

admin.site.register(Buechlein)
admin.site.register(Artikel)
admin.site.register(MarkdownArtikel)
