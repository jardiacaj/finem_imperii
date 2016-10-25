from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from world.views import CharacterCreationView, activate_character

urlpatterns = [
    url(r'^create_character/?$', login_required(CharacterCreationView.as_view()), name='create_character'),
    url(r'^activate_character/(?P<char_id>[0-9]+)$', activate_character, name='activate_character'),
]
