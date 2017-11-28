from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from base.utils import redirect_back
from decorators import inchar_required
from organization.models.document import PolicyDocument
from organization.models.capability import Capability
from organization.views.proposal import capability_success


class DocumentCapabilityView(View):
    def get(self, request, capability_id, document_id=None):
        capability = get_object_or_404(
            Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
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
        if 'delete' in request.POST.keys() and document_id is None:
            return redirect_back(request, reverse('character:character_home'),
                                 error_message="You cannot do that")

        capability = get_object_or_404(
            Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
        if document_id is None:
            new_document = True
        else:
            document = get_object_or_404(PolicyDocument, id=document_id)
            new_document = False

        proposal = {
            'new': new_document,
            'document_id': None if new_document else document.id,
            'delete': 'delete' in request.POST.keys(),
            'title': request.POST.get('title'),
            'body': request.POST.get('body'),
            'public': request.POST.get('public'),
        }
        capability.create_proposal(request.hero, proposal)
        return capability_success(capability, request)


@inchar_required
def document_view(request, document_id):
    document = get_object_or_404(PolicyDocument, id=document_id)
    hero_is_member = document.organization.character_is_member(request.hero)

    if not document.public and not hero_is_member:
        return redirect_back(request, reverse('character:character_home'),
                             error_message="You cannot view this document")

    context = {
        'document': document,
        'hero_is_member': hero_is_member,
    }
    return render(request, 'organization/view_document.html', context)