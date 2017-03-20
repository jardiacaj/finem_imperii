from django.conf.urls import url

from decorators import inchar_required
from organization.views import organization_view, document_view, capability_view, \
    DocumentCapabilityView, BanningCapabilityView

urlpatterns = [
    url(r'^(?P<organization_id>[0-9]+)$', organization_view, name='view'),
    url(r'^document/(?P<document_id>[0-9]+)$', document_view, name='document'),
    url(r'^capability/(?P<capability_id>[0-9]+)$', capability_view, name='capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/ban$',
        inchar_required(BanningCapabilityView.as_view()), name='banning_capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/document/(?P<document_id>[0-9]+)?$',
        inchar_required(DocumentCapabilityView.as_view()), name='document_capability'),
]
