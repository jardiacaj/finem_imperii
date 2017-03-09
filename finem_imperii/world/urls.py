from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from decorators import inchar_required
from world.views import CharacterCreationView, activate_character, character_home, setup_battle, world_view, \
    create_character, minimap_view, world_view_iframe, RecruitmentView, travel_view_iframe, TravelView, unit_view

urlpatterns = [
    url(r'^create_character$', create_character, name='create_character'),
    url(r'^create_character/(?P<world_id>[0-9]+)$', login_required(CharacterCreationView.as_view()), name='create_character'),
    url(r'^activate_character/(?P<char_id>[0-9]+)$', activate_character, name='activate_character'),
    url(r'^character_home$', character_home, name='character_home'),
    url(r'^travel/(?P<settlement_id>[0-9]+)?$', inchar_required(TravelView.as_view()), name='travel'),
    url(r'^travel_iframe/(?P<settlement_id>[0-9]+)?$', travel_view_iframe, name='travel_iframe'),
    url(r'^recruit$', inchar_required(RecruitmentView.as_view()), name='recruit'),
    url(r'^setup_battle/(?P<rival_char_id>[0-9]+)?$', setup_battle, name='setup_battle'),
    url(r'^world/(?P<world_id>[0-9]+)$', world_view, name='world'),
    url(r'^world_iframe/(?P<world_id>[0-9]+)$', world_view_iframe, name='world_iframe'),
    url(r'^unit/(?P<unit_id>[0-9]+)$', unit_view, name='unit'),
    url(r'^minimap$', minimap_view, name='minimap'),
]
