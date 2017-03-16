from django.conf.urls import url

from decorators import inchar_required
from organization.views import organization_view, organization_documents_list, document_view, capability_view, \
    DocumentCapabilityView

urlpatterns = [
    url(r'^(?P<organization_id>[0-9]+)$', organization_view, name='view'),
    url(r'^(?P<organization_id>[0-9]+)/documents$', organization_documents_list, name='documents'),
    url(r'^document/(?P<document_id>[0-9]+)$', document_view, name='document'),
    url(r'^capability/(?P<capability_id>[0-9]+)$', capability_view, name='capability'),
    url(r'^capability/(?P<capability_id>[0-9]+)/document/(?P<document_id>[0-9]+)?$',
        inchar_required(DocumentCapabilityView.as_view()), name='document_capability'),
]
