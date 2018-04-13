from django.contrib import admin

from .models import Spendenstufe, Kauf


class KaufAdmin(admin.ModelAdmin):
    list_filter = ['zeit']
    search_fields = ['nutzer__user__email']


admin.site.register(Spendenstufe)
admin.site.register(Kauf, KaufAdmin)
