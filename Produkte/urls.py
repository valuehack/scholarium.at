from django.conf.urls import url, include

from . import views, models
from django.views.generic import TemplateView, ListView
from Grundgeruest.views import TemplateMitMenue

app_name = 'Produkte'

urlpatterns = [
    url('^$',
        TemplateMitMenue.as_view(template_name='Produkte/warenkorb.html'), 
        name='warenkorb'),
    url('^kaufen$', views.kaufen, name='kaufen'),
    url('^bestellungen$', views.bestellungen, name='bestellungen'),
    url('^herunterladen$', views.medien_runterladen, name='runterladen'),
    
    url(r'^add/$', views.AddItem.as_view(), name='cart-add'), # ersetzt view aus:
    url('', include('easycart.urls')),
]
