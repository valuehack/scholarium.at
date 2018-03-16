from django.conf.urls import url

from .views import control_view, skripte_view, rechnung_view

app_name = 'Workflow'

urlpatterns = [
    url('^skripte/$', skripte_view, name='skripte'),
    url('^rechnungen/$', rechnung_view, name='rechnungen'),
    url(r'^$', control_view, name='index'),
]
