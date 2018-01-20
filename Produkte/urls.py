from django.conf.urls import url, include

from . import views
from Grundgeruest.views import TemplateMitMenue

app_name = 'Produkte'

urlpatterns = [
    url('^$',
        TemplateMitMenue.as_view(template_name='Produkte/warenkorb.html'), 
        name='warenkorb'),
    url('^kaufen$', views.kaufen, name='kaufen'),
    url('^bestellungen$', views.bestellungen, name='bestellungen'),
    url('^herunterladen$', views.medien_runterladen, name='runterladen'),
    
    url(r'^add/$', views.AddItem.as_view(), name='cart-add'), 
    url(r'^remove/$', views.RemoveItem.as_view(), name='cart-remove'), 
    url(r'^empty/$', views.EmptyCart.as_view(), name='cart-empty'),
    url(r'^change-quantity/$', views.ChangeItemQuantity.as_view(),
        name='cart-change-quantity'),
    # die vier ersetzen die views aus:
    url('', include('easycart.urls')),
]
