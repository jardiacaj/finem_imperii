from django.conf.urls import url

from battle.views import setup_view, test_view, create_test_battle

urlpatterns = [
    url(r'^setup/?$', setup_view, name='setup'),
    url(r'^test/?$', test_view, name='test'),
    url(r'^test2/?$', create_test_battle, name='test2'),
]
