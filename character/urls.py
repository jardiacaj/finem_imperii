from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from decorators import inchar_required
from character.views import create_character, CharacterCreationView, \
    activate_character, pause_character, unpause_character, character_home, \
    TravelView, travel_view_iframe, public_order, character_view, \
    character_view_iframe, InventoryView, transfer_cash

urlpatterns = [
    url(r'^create_character$', create_character, name='create_character'),
    url(r'^create_character/(?P<world_id>[0-9]+)$', login_required(CharacterCreationView.as_view()), name='create_character'),
    url(r'^activate_character/(?P<char_id>[0-9]+)$', activate_character, name='activate_character'),
    url(r'^pause_character$', pause_character, name='pause_character'),
    url(r'^unpause_character$', unpause_character, name='unpause_character'),
    url(r'^character_home$', character_home, name='character_home'),
    url(r'^travel/(?P<settlement_id>[0-9]+)?$', inchar_required(TravelView.as_view()), name='travel'),
    url(r'^travel_iframe/(?P<settlement_id>[0-9]+)?$', travel_view_iframe, name='travel_iframe'),
    url(r'^inventory$', inchar_required(InventoryView.as_view()), name='inventory'),
    url(r'^character/(?P<character_id>[0-9]+)$', character_view, name='character'),
    url(r'^character_iframe/(?P<character_id>[0-9]+)$', character_view_iframe, name='character_iframe'),
    url(r'^public_order$', public_order, name='public_order'),
    url(r'^transfer_cash$', transfer_cash, name='transfer_cash'),
]
