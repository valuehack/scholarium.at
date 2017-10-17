from django.conf.urls import url, include
from django.views.generic import ListView
from . import views

app_name = 'Notizen'

urlpatterns = [
    url(r'^$', 
        views.ZeigenUndEintragen.as_view(),
        {'liste_id': 1},
        name='liste'),
]
