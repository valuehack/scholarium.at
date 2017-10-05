from django.contrib import admin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from guardian.admin import GuardedModelAdmin
from userena.models import UserenaSignup
from userena import settings as userena_settings
from django.contrib.auth.models import Group

from .models import *

# Register your models here.

class UnterpunktInline(admin.TabularInline):
    model = Unterpunkt
    fields = ('bezeichnung', 'slug')
    extra = 1    

class HauptpunktAdmin(admin.ModelAdmin):
    inlines = [UnterpunktInline]

admin.site.register(Hauptpunkt, HauptpunktAdmin)
admin.site.register(Unterpunkt)
admin.site.register(Mitwirkende)


# von userena.admin kopiert und angepasst

class UserenaSignupInline(admin.StackedInline):
    model = UserenaSignup
    max_num = 1

class ProfileInline(admin.StackedInline):
    model = ScholariumProfile
    max_num = 1

class UserenaAdmin(UserAdmin, GuardedModelAdmin):
    inlines = [UserenaSignupInline, ProfileInline]
    list_display = ('email', 'first_name', 'last_name',
                    'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


#admin.site.unregister(get_user_model())
#admin.site.unregister(Group)
admin.site.register(get_user_model(), UserenaAdmin)
