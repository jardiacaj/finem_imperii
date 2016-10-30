from django.conf.urls import url

from battle.views import setup_view, view_battle, create_test_battle3

urlpatterns = [
    url(r'^setup/(?P<battle_id>[0-9]+)$', setup_view, name='setup'),
    url(r'^view/(?P<battle_id>[0-9]+)$', view_battle, name='view_battle'),
    url(r'^test3/?$', create_test_battle3, name='test3'),
]
