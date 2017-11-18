from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from decorators import inchar_required
from world.views import CharacterCreationView, activate_character, \
    character_home, world_view, \
    create_character, minimap_view, world_view_iframe, travel_view_iframe, \
    TravelView, character_view, tile_view, \
    tile_view_iframe, character_view_iframe, \
    InventoryView, public_order, pause_character, unpause_character, \
    transfer_cash

urlpatterns = [
    url(r'^create_character$', create_character, name='create_character'),
    url(r'^create_character/(?P<world_id>[0-9]+)$', login_required(CharacterCreationView.as_view()), name='create_character'),
    url(r'^activate_character/(?P<char_id>[0-9]+)$', activate_character, name='activate_character'),
    url(r'^pause_character$', pause_character, name='pause_character'),
    url(r'^unpause_character$', unpause_character, name='unpause_character'),
    url(r'^character_home$', character_home, name='character_home'),
    url(r'^travel/(?P<settlement_id>[0-9]+)?$', inchar_required(TravelView.as_view()), name='travel'),
    url(r'^travel_iframe/(?P<settlement_id>[0-9]+)?$', travel_view_iframe, name='travel_iframe'),
    url(r'^tile/(?P<tile_id>[0-9]+)$', tile_view, name='tile'),
    url(r'^tile_iframe/(?P<tile_id>[0-9]+)$', tile_view_iframe, name='tile_iframe'),
    url(r'^world/(?P<world_id>[0-9]+)$', world_view, name='world'),
    url(r'^world_iframe/(?P<world_id>[0-9]+)$', world_view_iframe, name='world_iframe'),
    url(r'^inventory$', inchar_required(InventoryView.as_view()), name='inventory'),
    url(r'^character/(?P<character_id>[0-9]+)$', character_view, name='character'),
    url(r'^character_iframe/(?P<character_id>[0-9]+)$', character_view_iframe, name='character_iframe'),
    url(r'^public_order$', public_order, name='public_order'),
    url(r'^minimap$', minimap_view, name='minimap'),
    url(r'^transfer_cash$', transfer_cash, name='transfer_cash'),
]
