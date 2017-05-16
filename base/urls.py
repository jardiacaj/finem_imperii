from django.conf.urls import url

from base.views import homepage

urlpatterns = [
    url(r'^$', homepage, name='home'),
]
