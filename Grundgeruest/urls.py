from django.conf.urls import url

from . import views

app_name = 'Grundgeruest'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    #url(r'^paypal_create_payment$', views.paypal_create_payment, name='paypal_create_payment'),    
    #url(r'^paypal_execute_payment$', views.paypal_execute_payment, name='paypal_execute_payment'),    
    url(r'^paypal_bestaetigung$', views.paypal_bestaetigung, name='paypal_bestaetigung'),    
    url(r'^(?P<slug>[\w-]+)/$', views.seite_rest, name='seite_rest'),
]
