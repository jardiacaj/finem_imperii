from django.conf.urls import url

from base.views import homepage, help_view

urlpatterns = [
    url(r'^$', homepage, name='home'),
    url(r'^help$', help_view, name='help'),
]
