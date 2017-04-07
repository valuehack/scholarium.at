from django.conf.urls import url, include

from . import views, models
from django.views.generic import TemplateView, ListView

app_name = 'Produkte'

urlpatterns = [
    url('^$',
        TemplateView.as_view(template_name='Produkte/warenkorb.html'), 
        name='warenkorb'),
    url('^add$', 
        ListView.as_view(
            template_name='Produkte/formular.html', 
            model=models.Produkt,
            context_object_name = 'produkte'),
        name='add_test',),
    url('^kaufen$', views.kaufen, name='kaufen'),
    url('^bestellungen$', views.bestellungen, name='bestellungen'),
    url('', include('easycart.urls')),
]
