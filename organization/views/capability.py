from django.contrib import messages
from django.db import transaction
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import View

from battle.models import BattleFormation
from messaging import shortcuts
from organization.models import Organization, PolicyDocument, Capability, \
    PositionCandidacy, PositionElectionVote, OrganizationRelationship, \
    MilitaryStance
from organization.views.decorator import capability_required_decorator
from world.models import Character, Tile, TileEvent, Settlement


def capability_success(capability, request):
    if capability.organization.decision_taking == Organization.DEMOCRATIC:
        messages.success(
            request,
            "A proposal has been created.",
            "success"
        )
    else:
        messages.success(request, "Done!", "success")
    return redirect(capability.organization.get_absolute_url())


@require_POST
@capability_required_decorator
def elect_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.ELECT)

    election = capability.applying_to.current_election

    if not election:
        messages.error(
            request,
            "There is no election in progress for {}".format(
                capability.applying_to
            ),
            "danger"
        )
        return redirect(capability.get_absolute_url())

    if capability.applying_to.current_election.positionelectionvote_set.filter(
            voter=request.hero).exists():
        messages.error(
            request,
            "You already issued a vote before.".format(capability.applying_to),
            "danger"
        )
        return redirect(capability.get_absolute_url())

    try:
        candidacy = PositionCandidacy.objects.get(
            id=int(request.POST.get('candidacy_id')),
            election=election,
            retired=False
        )
    except PositionCandidacy.DoesNotExist:
        messages.error(
            request, "That is not a valid candidacy to vote for.", "danger")
        return redirect(capability.get_absolute_url())

    PositionElectionVote.objects.create(
        election=election,
        voter=request.hero,
        candidacy=candidacy
    )

    messages.success(
        request,
        "You have issued your vote for {}".format(candidacy.candidate),
        "success"
    )
    return redirect(capability.get_absolute_url())


@require_POST
@capability_required_decorator
def heir_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.HEIR)

    first_heir_id = request.POST.get('first_heir')
    second_heir_id = request.POST.get('second_heir')

    try:
        first_heir = Character.objects.get(id=first_heir_id)
    except Character.DoesNotExist:
        first_heir = None

    try:
        second_heir = Character.objects.get(id=second_heir_id)
    except Character.DoesNotExist:
        second_heir = None

    if (
            first_heir not in capability.applying_to.get_heir_candidates()
            or
            first_heir == capability.applying_to.get_position_occupier()
    ):
        messages.error(request, "Invalid first heir", "danger")
        return redirect(capability.get_absolute_url())

    if (
            second_heir not in capability.applying_to.get_heir_candidates()
            or
            second_heir == capability.applying_to.get_position_occupier()
    ) and second_heir is not None:
        messages.error(request, "Invalid second heir", "danger")
        return redirect(capability.get_absolute_url())

    proposal = {
        'first_heir': first_heir.id,
        'second_heir': second_heir.id if second_heir is not None else 0
    }

    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


@require_POST
@capability_required_decorator
def election_convoke_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.CONVOKE_ELECTIONS)

    months_to_election = int(request.POST.get('months_to_election'))
    if not 6 <= months_to_election <= 16:
        messages.error(
            request,
            "The time period must be between 6 and 18 months",
            "danger"
        )
        return redirect(capability.get_absolute_url())

    proposal = {'months_to_election': months_to_election}
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


@require_POST
@capability_required_decorator
def candidacy_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.CANDIDACY)

    election = capability.applying_to.current_election
    if not election:
        messages.error(
            request, "There is currently no election in progress!", "danger")
        return redirect(capability.get_absolute_url())

    description = request.POST.get('description')
    retire = request.POST.get('retire')

    candidacy, new = PositionCandidacy.objects.get_or_create(
        election=election,
        candidate=request.hero
    )

    if retire:
        candidacy.retired = True
        messages.success(
            request, "Your candidacy has been retired.", "success")
    else:
        candidacy.description = description
        if new:
            messages.success(
                request, "Your candidacy has been created.", "success")
        else:
            messages.success(
                request, "Your candidacy has been updated.", "success")
    candidacy.save()

    message = shortcuts.create_message(
        'messaging/messages/elections_candidacy.html',
        capability.applying_to.world,
        'elections',
        {
            'candidacy': candidacy,
            'retire': retire,
            'new': new
        },
        link=election.get_absolute_url()
    )
    shortcuts.add_organization_recipient(
        message,
        capability.applying_to,
        add_lead_organizations=True
    )

    return redirect(capability.get_absolute_url())


@require_POST
@capability_required_decorator
def banning_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.BAN)

    character_to_ban = get_object_or_404(
        Character, id=request.POST.get('character_to_ban_id'))
    if character_to_ban not in capability.applying_to.character_members.all():
        messages.error(request, "You cannot do that", "danger")
        return redirect(request.META.get('HTTP_REFERER',
                                         reverse('world:character_home')))

    proposal = {'character_id': character_to_ban.id}
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


@require_POST
@capability_required_decorator
def conquest_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.CONQUEST)
    tile_to_conquer = get_object_or_404(Tile, id=request.POST.get('tile_to_conquest_id'))

    if request.POST.get('stop'):
        try:
            tile_event = TileEvent.objects.get(
                tile=tile_to_conquer,
                organization=capability.applying_to,
                end_turn__isnull=True
            )
        except TileEvent.DoesNotExist:
            raise Http404
    else:
        if tile_to_conquer not in capability.applying_to.conquestable_tiles():
            raise Http404

    proposal = {
        'tile_id': tile_to_conquer.id,
        'stop': request.POST.get('stop')
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


@require_POST
@capability_required_decorator
def guilds_settings_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.GUILDS)
    settlement = get_object_or_404(
        Settlement, id=request.POST.get('settlement_id'))
    target_option = request.POST.get('option')

    if target_option not in [choice[0] for choice in Settlement.GUILDS_CHOICES]:
        raise Http404("Chosen option not valid")

    if (settlement.tile not in
            capability.applying_to.get_all_controlled_tiles()):
        raise Http404("Settlement not under control")

    proposal = {
        'settlement_id': settlement.id,
        'option': target_option
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


def check_line_formation_validity(request):
    element_size = int(request.POST['line_depth'])
    spacing = int(request.POST['line_spacing'])
    if not 0 < element_size <= 10 or not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing


def check_column_formation_validity(request):
    element_size = int(request.POST['column_width'])
    spacing = int(request.POST['column_spacing'])
    if not 0 < element_size <= 10 or not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing


def check_square_wedge_iwedge_formation_validity(request):
    element_size = None
    spacing = int(request.POST['square_spacing'])
    if not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing

formation_validity_checks = {
    BattleFormation.LINE: check_line_formation_validity,
    BattleFormation.COLUMN: check_column_formation_validity,
    BattleFormation.SQUARE: check_square_wedge_iwedge_formation_validity,
    BattleFormation.WEDGE: check_square_wedge_iwedge_formation_validity,
    BattleFormation.IWEDGE: check_square_wedge_iwedge_formation_validity,
}


@require_POST
@capability_required_decorator
def formation_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.BATTLE_FORMATION)

    new_formation = request.POST['new_formation']
    if new_formation not in formation_validity_checks.keys():
        raise Http404("Invalid formation")
    else:
        element_size, spacing = formation_validity_checks[new_formation](
            request)

    proposal = {
        'formation': new_formation,
        'spacing': spacing,
        'element_size': element_size
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)


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
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER',
                                             reverse('world:character_home')))

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
                'target_relationship': target_organization.get_relationship_to(capability.applying_to).desired_relationship
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
            if target_relationship not in [choice[0] for choice in OrganizationRelationship.RELATIONSHIP_CHOICES]:
                return self.fail_post_with_error(
                    capability_id, request, target_organization_id)
            proposal = {
                'type': 'propose',
                'target_organization_id': target_organization.id,
                'target_relationship': target_relationship
            }

        capability.create_proposal(request.hero, proposal)
        return capability_success(capability, request)


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
