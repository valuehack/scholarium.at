from django.conf.urls import url

from . import views

app_name = 'Grundgeruest'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<slug>[\w-]+)/$', views.seite_rest, name='seite_rest'),
]
