from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from decorators import inchar_required
from world.views import CharacterCreationView, activate_character, character_home, RecruitView, setup_battle, world_view, \
    create_character, minimap_view

urlpatterns = [
    url(r'^create_character/?$', create_character, name='create_character'),
    url(r'^create_character/(?P<world_id>[0-9]+)$', login_required(CharacterCreationView.as_view()), name='create_character'),
    url(r'^activate_character/(?P<char_id>[0-9]+)$', activate_character, name='activate_character'),
    url(r'^character_home/?$', character_home, name='character_home'),
    url(r'^recruit/?$', inchar_required(RecruitView.as_view()), name='recruit'),
    url(r'^setup_battle/(?P<rival_char_id>[0-9]+)?/?$', setup_battle, name='setup_battle'),
    url(r'^world/(?P<world_id>[0-9]+)/?$', world_view, name='world'),
    url(r'^minimap/(?P<world_id>[0-9]+)/(?P<tile_id>[0-9]+)?/(?P<settlement_id>[0-9]+)?$', minimap_view, name='minimap'),
]
