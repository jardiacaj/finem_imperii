from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from decorators import inchar_required
from organization.models import Organization, OrganizationRelationship, \
    PolicyDocument, PositionElection


@inchar_required
def organization_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    context = {
        'organization': organization,
        'hero_is_member': organization.character_is_member(request.hero),
        'can_use_capabilities': organization.character_can_use_capabilities(
            request.hero),
        'relationships': organization.relationships_stemming.exclude(
            relationship=OrganizationRelationship.PEACE),
    }
    return render(request, 'organization/view_organization.html', context)


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


@inchar_required
def election_list_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)

    context = {
        'organization': organization,
    }
    return render(request, 'organization/election_list.html', context)


@inchar_required
def election_view(request, election_id):
    election = get_object_or_404(PositionElection, id=election_id)

    context = {
        'election': election,
    }
    return render(request, 'organization/view_election.html', context)