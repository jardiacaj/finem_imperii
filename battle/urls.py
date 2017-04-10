from django.conf.urls import url

from battle.views import view_battle

urlpatterns = [
    url(r'^view/(?P<battle_id>[0-9]+)$', view_battle, name='view_battle'),
]
