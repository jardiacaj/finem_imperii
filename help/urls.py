from django.conf.urls import url
from django.views.generic.base import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='help/home.html'), name='home'),
    url(r'^fundamental$', TemplateView.as_view(template_name='help/fundamental.html'), name='fundamental'),
    url(r'^design', TemplateView.as_view(template_name='help/design.html'), name='design'),
    url(r'^mechanics', TemplateView.as_view(template_name='help/mechanics.html'), name='mechanics'),
    url(r'^about$', TemplateView.as_view(template_name='help/about.html'), name='about'),
]
