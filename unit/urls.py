from django.conf.urls import url

from decorators import inchar_required
from unit.views import RecruitmentView, unit_battle_orders, unit_status_change, \
    unit_conquest_action, unit_disband, unit_view, unit_rename, \
    unit_battle_settings

urlpatterns = [
    url(r'^recruit$', inchar_required(RecruitmentView.as_view()), name='recruit'),
    url(r'^(?P<unit_id>[0-9]+)$', unit_view, name='unit'),
    url(r'^(?P<unit_id>[0-9]+)/rename$', unit_rename, name='rename_unit'),
    url(r'^(?P<unit_id>[0-9]+)/battle_settings', unit_battle_settings, name='battle_settings_unit'),
    url(r'^(?P<unit_id>[0-9]+)/battle_orders$', unit_battle_orders, name='battle_orders_unit'),
    url(r'^(?P<unit_id>[0-9]+)/disband', unit_disband, name='unit_disband'),
    url(r'^(?P<unit_id>[0-9]+)/conquest', unit_conquest_action, name='unit_conquest_action'),
    url(r'^(?P<unit_id>[0-9]+)/(?P<new_status>[ a-z]+)', unit_status_change, name='unit_status_change'),
]
