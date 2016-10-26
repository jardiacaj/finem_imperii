from django.conf.urls import url

from battle.views import setup_view, test_view, create_test_battle, view_battle, create_test_battle3

urlpatterns = [
    url(r'^setup/?$', setup_view, name='setup'),
    url(r'^view/(?P<battle_id>[0-9]+)$', view_battle, name='view_battle'),
    url(r'^test/?$', test_view, name='test'),
    url(r'^test2/?$', create_test_battle, name='test2'),
    url(r'^test3/?$', create_test_battle3, name='test3'),
]
