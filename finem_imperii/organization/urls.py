from django.conf.urls import url

from decorators import inchar_required
from organization.views import organization_view, document_view, capability_view, \
    DocumentCapabilityView, ProposalView, election_convoke_view, capability_required_decorator, \
    banning_view, candidacy_view

urlpatterns = [
    url(r'^(?P<organization_id>[0-9]+)$', organization_view, name='view'),
    url(r'^document/(?P<document_id>[0-9]+)$', document_view, name='document'),
    url(r'^proposal/(?P<proposal_id>[0-9]+)$', inchar_required(ProposalView.as_view()), name='proposal'),
    url(r'^capability/(?P<capability_id>[0-9]+)$', capability_view, name='capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/ban$', banning_view, name='banning_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/convoke_elections', election_convoke_view, name='election_convoke_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/candidacy', candidacy_view, name='candidacy_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/document/(?P<document_id>[0-9]+)?$',
        inchar_required(capability_required_decorator(DocumentCapabilityView.as_view())), name='document_capability'),
]
