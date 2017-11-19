from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from organization.models import Capability, Organization, \
    OrganizationRelationship
from organization.views.proposal import capability_success


class DiplomacyCapabilityView(View):
    def get(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(
            Capability, id=capability_id, type=Capability.DIPLOMACY
        )
        target_organization = get_object_or_404(
            Organization, id=target_organization_id, barbaric=False
        )

        context = {
            'capability': capability,
            'target_organization': target_organization,
            'relationship_out': capability.applying_to.get_relationship_to(
                target_organization),
            'relationship_in': capability.applying_to.get_relationship_from(
                target_organization),
            'subtemplate': 'organization/capabilities/diplomacy_target.html',
        }
        return render(request, 'organization/capability.html', context)

    def fail_post_with_error(self, capability_id, request,
                             target_organization_id,
                             message="You cannot do that"):
        messages.error(request, message, "danger")
        return redirect(reverse(
            'organization:diplomacy_capability',
            kwargs={
                'capability_id': capability_id,
                'target_organization_id': target_organization_id}
        ))

    @transaction.atomic
    def post(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(
            Capability, id=capability_id, type=Capability.DIPLOMACY
        )
        target_organization = get_object_or_404(
            Organization, id=target_organization_id, barbaric=False
        )

        target_relationship = request.POST.get('target_relationship')

        if target_relationship in ("accept", "refuse"):
            if not target_organization.get_relationship_to(
                    capability.applying_to).is_proposal():
                return self.fail_post_with_error(
                    capability_id, request, target_organization_id)
            proposal = {
                'type': target_relationship,
                'target_organization_id': target_organization.id,
                'target_relationship': target_organization.get_relationship_to(
                    capability.applying_to).desired_relationship
            }
        elif target_relationship == "take back":
            if not capability.applying_to.get_relationship_to(
                    target_organization).is_proposal():
                return self.fail_post_with_error(
                    capability_id, request, target_organization_id)
            proposal = {
                'type': target_relationship,
                'target_organization_id': target_organization.id,
                'target_relationship':
                    capability.applying_to.get_relationship_to(
                        target_organization).desired_relationship
            }
        else:
            if capability.applying_to.get_relationship_to(
                    target_organization).is_proposal():
                return self.fail_post_with_error(
                    capability_id, request, target_organization_id)
            if target_relationship not in [
                choice[0] for choice in
                OrganizationRelationship.RELATIONSHIP_CHOICES
            ]:
                return self.fail_post_with_error(
                    capability_id, request, target_organization_id)
            proposal = {
                'type': 'propose',
                'target_organization_id': target_organization.id,
                'target_relationship': target_relationship
            }

        capability.create_proposal(request.hero, proposal)
        return capability_success(capability, request)
