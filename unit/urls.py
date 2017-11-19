from django.conf.urls import url

from decorators import inchar_required
from unit.views.actions import disband, conquest_action, rename
from unit.views.recruitment import RecruitmentView
from unit.views.settings import battle_settings, battle_orders, status_change
from unit.views.unit import unit_view

urlpatterns = [
    url(r'^recruit$', inchar_required(RecruitmentView.as_view()), name='recruit'),
    url(r'^(?P<unit_id>[0-9]+)$', unit_view, name='unit'),
    url(r'^(?P<unit_id>[0-9]+)/rename$', rename, name='rename'),
    url(r'^(?P<unit_id>[0-9]+)/battle_settings', battle_settings, name='battle_settings'),
    url(r'^(?P<unit_id>[0-9]+)/battle_orders$', battle_orders, name='battle_orders'),
    url(r'^(?P<unit_id>[0-9]+)/disband', disband, name='disband'),
    url(r'^(?P<unit_id>[0-9]+)/conquest', conquest_action, name='conquest_action'),
    url(r'^(?P<unit_id>[0-9]+)/(?P<new_status>[ a-z]+)', status_change, name='status_change'),
]
