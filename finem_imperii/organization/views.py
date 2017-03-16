from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse

from decorators import inchar_required
from organization.models import Organization, PolicyDocument, Capability


@inchar_required
def organization_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    context = {
        'organization': organization,
        'hero_is_member': organization.character_is_member(request.hero),
    }
    return render(request, 'organization/view_organization.html', context)


@inchar_required
def organization_documents_list(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    context = {
        'organization': organization,
        'hero_is_member': organization.character_is_member(request.hero),
        'hero_has_document_cap': organization.character_has_capability(request.hero, Capability.POLICY_DOCUMENT)
    }
    return render(request, 'organization/view_documents.html', context)


@inchar_required
def document_view(request, document_id):
    document = get_object_or_404(PolicyDocument, id=document_id)
    hero_is_member = document.organization.character_is_member(request.hero)

    if not document.public and not hero_is_member:
        messages.error(request, "You cannot view this document", "danger")
        return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    context = {
        'document': document,
        'hero_is_member': hero_is_member,
    }
    return render(request, 'organization/view_document.html', context)
