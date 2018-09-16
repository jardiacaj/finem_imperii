from django.conf.urls import url
from django.views.generic.base import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='help/home.html'), name='home'),
    url(r'^fundamental$', TemplateView.as_view(template_name='help/fundamental.html'), name='fundamental'),
    url(r'concepts', TemplateView.as_view(template_name='help/concepts.html'), name='concepts'),
    url(r'^mechanics', TemplateView.as_view(template_name='help/mechanics.html'), name='mechanics'),
    url(r'^about$', TemplateView.as_view(template_name='help/about.html'), name='about'),
]
