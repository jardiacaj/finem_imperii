from django.conf.urls import url

from organization.views import organization_view, documents_view

urlpatterns = [
    url(r'^organization/(?P<organization_id>[0-9]+)$', organization_view, name='view'),
    url(r'^organization/(?P<organization_id>[0-9]+)/documents$', documents_view, name='documents'),
]
