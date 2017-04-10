from django.conf.urls import url

from battle.views import battlefield_view, info_view

urlpatterns = [
    url(r'^info/(?P<battle_id>[0-9]+)$', info_view, name='info'),
    url(r'^battlefield/(?P<battle_id>[0-9]+)$', battlefield_view, name='battlefield'),
]
