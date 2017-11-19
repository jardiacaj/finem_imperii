from django.contrib import messages
from django.http.response import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from decorators import inchar_required
from organization.models import Organization, OrganizationRelationship


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
@require_POST
def leave_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)

    if request.hero not in organization.character_members.all():
        raise Http404("Hero is not a member")

    organization.remove_member(request.hero)

    messages.success(request, "You left {}".format(organization), "success")
    return redirect(organization.get_absolute_url())
