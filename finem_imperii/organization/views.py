from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse
from django.views.generic.base import View

from decorators import inchar_required
from organization.models import Organization, PolicyDocument, Capability
from world.models import Character


@inchar_required
def organization_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    context = {
        'organization': organization,
        'hero_is_member': organization.character_is_member(request.hero),
        'can_use_capabilities': organization.character_can_use_capabilities(request.hero),
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
def capability_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id)
    if not capability.organization.character_can_use_capabilities(request.hero):
        messages.error(request, "You cannot do that", "danger")
        return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    context = {
        'capability': capability,
        'subtemplate': 'organization/capabilities/{}.html'.format(capability.type),
    }
    return render(request, 'organization/capability.html', context)


class BanningCapabilityView(View):
    def check(self, request, capability_id):
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.BAN)
        if not capability.organization.character_can_use_capabilities(request.hero):
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    def get(self, request, capability_id):
        messages.error(request, "You cannot do that", "danger")
        return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    def post(self, request, capability_id):
        check_result = self.check(request, capability_id)
        if check_result is not None:
            return check_result
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.BAN)

        character_to_ban = get_object_or_404(Character, id=request.POST.get('character_to_ban_id'))
        if character_to_ban not in capability.applying_to.character_members.all():
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

        proposal = {'character_id': character_to_ban.id}

        capability.create_proposal(request.hero, proposal)

        if capability.organization.decision_taking == Organization.DEMOCRATIC:
            messages.success(request, "A vote has been started regarding your action", "success")
        else:
            messages.success(request, "Done!", "success")
        return redirect(capability.organization.get_absolute_url())


class DocumentCapabilityView(View):
    def check(self, request, capability_id, document_id):
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
        if not capability.organization.character_can_use_capabilities(request.hero):
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

        if 'delete' in request.POST.keys() and document_id is None:
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    def get(self, request, capability_id, document_id=None):
        check_result = self.check(request, capability_id, document_id)
        if check_result is not None:
            return check_result

        capability = get_object_or_404(Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
        if document_id is None:
            document = PolicyDocument(organization=capability.applying_to)
            new_document = True
        else:
            document = get_object_or_404(PolicyDocument, id=document_id)
            new_document = False

        context = {
            'capability': capability,
            'document': document,
            'new_document': new_document,
            'subtemplate': 'organization/capabilities/document.html',
        }
        return render(request, 'organization/capability.html', context)

    def post(self, request, capability_id, document_id=None):
        check_result = self.check(request, capability_id, document_id)
        if check_result is not None:
            return check_result

        capability = get_object_or_404(Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
        if document_id is None:
            new_document = True
        else:
            document = get_object_or_404(PolicyDocument, id=document_id)
            new_document = False

        proposal = {
            'new': new_document,
            'document_id': document_id,
            'delete': 'delete' in request.POST.keys(),
            'title': request.POST.get('title'),
            'body': request.POST.get('body'),
            'public': request.POST.get('public'),
        }

        capability.create_proposal(request.hero, proposal)

        if capability.organization.decision_taking == Organization.DEMOCRATIC:
            messages.success(request, "A vote has been started regarding your action", "success")
        else:
            messages.success(request, "Done!", "success")
        return redirect(capability.organization.get_absolute_url())
