from django.conf.urls import url

from decorators import inchar_required
from organization.views.capability import banning_view, conquest_view, \
    guilds_settings_view, formation_view, election_convoke_view, \
    candidacy_view, \
    elect_view, DocumentCapabilityView, DiplomacyCapabilityView, \
    MilitaryStanceCapabilityView, heir_view
from organization.views.decorator import capability_required_decorator
from organization.views.generic_capability import ProposalView, CapabilityView
from organization.views.regular import organization_view, election_list_view, \
    election_view, document_view, leave_view

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
        banning_view, name='banning_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/conquer',
        conquest_view, name='conquest_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/guilds',
        guilds_settings_view, name='guilds_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/formation',
        formation_view, name='battle_formation_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/convoke_elections',
        election_convoke_view, name='election_convoke_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/candidacy',
        candidacy_view, name='candidacy_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/elect',
        elect_view, name='elect_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/heir',
        heir_view, name='heir_capability'),
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
