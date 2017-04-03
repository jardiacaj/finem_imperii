from django.conf.urls import url

from battle.views import setup_view, view_battle, set_orders, ready_view

urlpatterns = [
    url(r'^setup/(?P<battle_id>[0-9]+)$', setup_view, name='setup'),
    url(r'^ready/(?P<battle_character_id>[0-9]+)$', ready_view, name='ready'),
    url(r'^view/(?P<battle_id>[0-9]+)$', view_battle, name='view_battle'),
    url(r'^set_orders/(?P<battle_unit_id>[0-9]+)$', set_orders, name='set_orders'),
]
