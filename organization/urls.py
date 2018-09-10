from django.conf.urls import url

from decorators import inchar_required
from organization.views.heir import heir_capability_view
from organization.views.ban import banning_capability_view
from organization.views.conquest import conquest_capability_view
from organization.views.guilds import guilds_settings_capability_view
from organization.views.document import DocumentCapabilityView, document_view
from organization.views.diplomacy import DiplomacyCapabilityView
from organization.views.military_stance import MilitaryStanceCapabilityView
from organization.views.battle_formation import formation_capability_view
from organization.views.elections import elect_capability_view, \
    election_convoke_capability_view, \
    present_candidacy_capability_view, election_list_view, election_view
from organization.views.decorator import capability_required_decorator
from organization.views.arrest_warrant import arrest_warrant_capability_view, \
    arrest_warrant_revoke_capability_view
from organization.views.proposal import ProposalView
from organization.views.capability import CapabilityView
from organization.views.organization import organization_view, leave_view

urlpatterns = [
    url(r'^(?P<organization_id>[0-9]+)$',
        organization_view, name='view'),
    url(r'^(?P<organization_id>[0-9]+)/elections$',
        election_list_view, name='election_list'),
    url(r'^(?P<organization_id>[0-9]+)/leave',
        leave_view, name='leave'),
    url(r'^election/(?P<election_id>[0-9]+)$',
        election_view, name='election'),
    url(r'^document/(?P<document_id>[0-9]+)$',
        document_view, name='document'),
    url(r'^proposal/(?P<proposal_id>[0-9]+)$',
        inchar_required(ProposalView.as_view()), name='proposal'),
    url(r'^capability/(?P<capability_id>[0-9]+)$',
        inchar_required(capability_required_decorator(CapabilityView.as_view())),
        name='capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/ban$',
        banning_capability_view, name='banning_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/arrest_warrant',
        arrest_warrant_capability_view, name='arrest_warrant_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/revoke_warrant/(?P<warrant_id>[0-9]+)',
        arrest_warrant_revoke_capability_view, name='arrest_warrant_revoke_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/conquer',
        conquest_capability_view, name='conquest_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/guilds',
        guilds_settings_capability_view, name='guilds_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/formation',
        formation_capability_view, name='battle_formation_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/convoke_elections',
        election_convoke_capability_view, name='election_convoke_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/candidacy',
        present_candidacy_capability_view, name='candidacy_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/elect',
        elect_capability_view, name='elect_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/heir',
        heir_capability_view, name='heir_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/document/(?P<document_id>[0-9]+)?$',
        inchar_required(capability_required_decorator(DocumentCapabilityView.as_view())),
        name='document_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/diplomacy/(?P<target_organization_id>[0-9]+)$',
        inchar_required(capability_required_decorator(DiplomacyCapabilityView.as_view())),
        name='diplomacy_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/stance/(?P<target_organization_id>[0-9]+)$',
        inchar_required(capability_required_decorator(MilitaryStanceCapabilityView.as_view())),
        name='military_stance_capability'),
]
