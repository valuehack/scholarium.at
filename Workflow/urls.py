from django.conf.urls import url

from .views import control_view

app_name = 'Workflow'

urlpatterns = [
    url('^skripte$', control_view, name='skripte'),
]
