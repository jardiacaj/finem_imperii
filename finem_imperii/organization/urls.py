from django.conf.urls import url

from organization.views import organization_view, organization_documents_list, document_view

urlpatterns = [
    url(r'^organization/(?P<organization_id>[0-9]+)$', organization_view, name='view'),
    url(r'^organization/(?P<organization_id>[0-9]+)/documents$', organization_documents_list, name='documents'),
    url(r'^document/(?P<document_id>[0-9]+)$', document_view, name='document'),
]
