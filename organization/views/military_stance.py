from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from organization.models.relationship import MilitaryStance
from organization.models.capability import Capability
from organization.models.organization import Organization
from organization.views.proposal import capability_success
from world.models.geography import Tile


class MilitaryStanceCapabilityView(View):
    def get(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(
            Capability, id=capability_id, type=Capability.MILITARY_STANCE)
        target_organization = get_object_or_404(
            Organization, id=target_organization_id, violence_monopoly=True)
        regions = list(
            capability.applying_to.world.tile_set.exclude(
                type__in=(Tile.DEEPSEA, Tile.SHORE)
            ).order_by('name')
        )
        for region in regions:
            region.stance = capability.applying_to.get_region_stance_to(
                target_organization, region)

        context = {
            'capability': capability,
            'target_organization': target_organization,
            'stance': capability.applying_to.get_default_stance_to(
                target_organization),
            'regions': regions,
            'subtemplate': 'organization/capabilities/'
                           'military stance_target.html',
        }
        return render(request, 'organization/capability.html', context)

    @transaction.atomic
    def post(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(
            Capability,
            id=capability_id,
            type=Capability.MILITARY_STANCE
        )
        target_organization = get_object_or_404(
            Organization,
            id=target_organization_id,
            world=capability.applying_to.world,
            violence_monopoly=True
        )
        target_stance = request.POST.get('new_stance')
        if target_stance not in [o[0] for o in MilitaryStance.STANCE_CHOICES]:
            raise Http404()

        proposal = {
            'target_organization_id': target_organization.id,
            'target_stance': target_stance,
        }

        if 'region_id' in request.POST.keys():
            region = get_object_or_404(
                Tile,
                id=request.POST['region_id'],
                world=capability.applying_to.world
            )
            if not region.is_on_ground():
                raise Http404()
            proposal['region_id'] = region.id

        capability.create_proposal(request.hero, proposal)
        capability_success(capability, request)
        return redirect(reverse(
            'organization:military_stance_capability',
            kwargs={
                'capability_id': capability_id,
                'target_organization_id': target_organization_id
            })
        )
