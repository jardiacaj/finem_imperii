import json

from django.contrib import messages
from django.db import transaction
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls.base import reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import View

from battle.models import BattleFormation
from decorators import inchar_required
from organization.models import Organization, PolicyDocument, Capability, CapabilityProposal, CapabilityVote, \
    PositionCandidacy, PositionElectionVote, PositionElection, OrganizationRelationship, MilitaryStance
from world.models import Character, Tile


@inchar_required
def organization_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    context = {
        'organization': organization,
        'hero_is_member': organization.character_is_member(request.hero),
        'can_use_capabilities': organization.character_can_use_capabilities(request.hero),
        'relationships': organization.relationships_stemming.exclude(relationship=OrganizationRelationship.PEACE),
    }
    return render(request, 'organization/view_organization.html', context)


def capability_required_decorator(func):
    @inchar_required
    def inner(*args, **kwargs):
        def fail_the_request(*args, **kwargs):
            messages.error(args[0], "You cannot do that", "danger")
            return redirect(args[0].META.get('HTTP_REFERER', reverse('world:character_home')))
        capability_id = kwargs.get('capability_id')
        if capability_id is None:
            capability_id = args[0].GET.get('capability_id')
        if capability_id is None:
            capability_id = args[0].POST.get('capability_id')
        capability = get_object_or_404(Capability, id=capability_id)
        if not capability.organization.character_can_use_capabilities(args[0].hero):
            return fail_the_request(*args, **kwargs)
        return func(*args, **kwargs)
    return inner


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


@capability_required_decorator
def capability_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id)
    if not capability.organization.character_can_use_capabilities(request.hero):
        messages.error(request, "You cannot do that", "danger")
        return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    context = {
        'capability': capability,
        'subtemplate': 'organization/capabilities/{}.html'.format(capability.type),
    }

    if capability.type == Capability.CANDIDACY:
        context['heros_candidacy'] = None
        if capability.applying_to.current_election:
            try:
                context['heros_candidacy'] = capability.applying_to.current_election.positioncandidacy_set.get(candidate=request.hero)
            except PositionCandidacy.DoesNotExist:
                pass

    if capability.type == Capability.ELECT:
        context['heros_vote'] = None
        if capability.applying_to.current_election:
            try:
                context['heros_vote'] = capability.applying_to.current_election.positionelectionvote_set.get(voter=request.hero)
            except PositionElectionVote.DoesNotExist:
                pass

    if capability.type == Capability.DIPLOMACY:
        if capability.applying_to.violence_monopoly:
            context['states'] = []
            for state in capability.applying_to.world.get_violence_monopolies():
                if state == capability.applying_to:
                    continue
                state.relationship_out = state.get_relationship_from(capability.applying_to)
                state.relationship_in = state.get_relationship_to(capability.applying_to)
                context['states'].append(state)

    if capability.type == Capability.MILITARY_STANCE:
        if capability.applying_to.violence_monopoly:
            context['states'] = []
            for state in capability.applying_to.world.get_violence_monopolies():
                if state == capability.applying_to:
                    continue
                state.default_stance = capability.applying_to.get_default_stance_to(state)
                state.region_stances = capability.applying_to.get_region_stances_to(state)
                context['states'].append(state)

    if capability.type == Capability.CONQUEST:
        if capability.applying_to.violence_monopoly:
            candidate_tiles = Tile.objects\
                .filter(world=capability.applying_to.world)\
                .exclude(controlled_by=capability.applying_to)\
                .exclude(type__in=(Tile.SHORE, Tile.DEEPSEA))
            context['conquestable_tiles'] = []
            for tile in candidate_tiles:
                if tile.get_units().filter(owner_character__in=capability.applying_to.character_members.all()):
                    context['conquestable_tiles'].append(tile)

    return render(request, 'organization/capability.html', context)


@require_POST
@capability_required_decorator
def elect_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id, type=Capability.ELECT)

    election = capability.applying_to.current_election

    if not election:
        messages.error(request, "There is no election in progress for {}".format(capability.applying_to), "danger")
        return redirect(capability.get_absolute_url())

    if capability.applying_to.current_election.positionelectionvote_set.filter(voter=request.hero).exists():
        messages.error(request, "You already issued a vote before.".format(capability.applying_to), "danger")
        return redirect(capability.get_absolute_url())

    try:
        candidacy = PositionCandidacy.objects.get(
            id=int(request.POST.get('candidacy_id')),
            election=election,
            retired=False
        )
    except PositionCandidacy.DoesNotExist:
        messages.error(request, "That is not a valid candidacy to vote for.", "danger")
        return redirect(capability.get_absolute_url())

    PositionElectionVote.objects.create(
        election=election,
        voter=request.hero,
        candidacy=candidacy
    )

    messages.success(request, "You have issued your vote for {}".format(candidacy.candidate), "success")
    return redirect(capability.get_absolute_url())


@require_POST
@capability_required_decorator
def election_convoke_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id, type=Capability.CONVOKE_ELECTIONS)

    months_to_election = int(request.POST.get('months_to_election'))
    if not 6 <= months_to_election <= 16:
        messages.error(request, "The time period must be between 6 and 18 months", "danger")
        return redirect(capability.get_absolute_url())

    proposal = {'months_to_election': months_to_election}

    capability.create_proposal(request.hero, proposal)

    if capability.organization.decision_taking == Organization.DEMOCRATIC:
        messages.success(request, "A vote has been started regarding your action", "success")
    else:
        messages.success(request, "Done!", "success")
    return redirect(capability.organization.get_absolute_url())


@require_POST
@capability_required_decorator
def candidacy_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id, type=Capability.CANDIDACY)

    election = capability.applying_to.current_election
    if not election:
        messages.error(request, "There is currently no election in progress!", "danger")
        return redirect(capability.get_absolute_url())

    description = request.POST.get('description')
    retire = request.POST.get('retire')

    candidacy, new = PositionCandidacy.objects.get_or_create(
        election=election,
        candidate=request.hero
    )

    if retire:
        candidacy.retired = True
        messages.success(request, "Your candidacy has been retired.", "success")
    else:
        candidacy.description = description
        if new:
            messages.success(request, "Your candidacy has been created.", "success")
        else:
            messages.success(request, "Your candidacy has been updated.", "success")
    candidacy.save()

    return redirect(capability.get_absolute_url())


@require_POST
@capability_required_decorator
def banning_view(request, capability_id):
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


@require_POST
@capability_required_decorator
def formation_view(request, capability_id):
    capability = get_object_or_404(Capability, id=capability_id, type=Capability.BATTLE_FORMATION)

    new_formation = request.POST['new_formation']
    if new_formation == BattleFormation.LINE:
        element_size = int(request.POST['line_depth'])
        spacing = int(request.POST['line_spacing'])
        if not 0 < element_size <= 10 or not spacing <= 15:
            raise Http404("Invalid settings")
    elif new_formation == BattleFormation.COLUMN:
        element_size = int(request.POST['column_width'])
        spacing = int(request.POST['column_spacing'])
        if not 0 < element_size <= 10 or not spacing <= 15:
            raise Http404("Invalid settings")
    elif new_formation == BattleFormation.SQUARE:
        element_size = None
        spacing = int(request.POST['square_spacing'])
        if not spacing <= 15:
            raise Http404("Invalid settings")
    elif new_formation == BattleFormation.WEDGE:
        element_size = None
        spacing = int(request.POST['wedge_spacing'])
        if not spacing <= 15:
            raise Http404("Invalid settings")
    elif new_formation == BattleFormation.IWEDGE:
        element_size = None
        spacing = int(request.POST['iwedge_spacing'])
        if not spacing <= 15:
            raise Http404("Invalid settings")
    else:
        raise Http404("Invalid formation")

    proposal = {
        'formation': new_formation,
        'spacing': spacing,
        'element_size': element_size
    }

    capability.create_proposal(request.hero, proposal)

    if capability.organization.decision_taking == Organization.DEMOCRATIC:
        messages.success(request, "A vote has been started regarding your action", "success")
    else:
        messages.success(request, "Done!", "success")
    return redirect(capability.get_absolute_url())


class DocumentCapabilityView(View):
    def get(self, request, capability_id, document_id=None):
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
        if 'delete' in request.POST.keys() and document_id is None:
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

        capability = get_object_or_404(Capability, id=capability_id, type=Capability.POLICY_DOCUMENT)
        if document_id is None:
            new_document = True
        else:
            document = get_object_or_404(PolicyDocument, id=document_id)
            new_document = False

        proposal = {
            'new': new_document,
            'document_id': document.id,
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


class DiplomacyCapabilityView(View):
    def get(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.DIPLOMACY)
        target_organization = get_object_or_404(Organization, id=target_organization_id)

        context = {
            'capability': capability,
            'target_organization': target_organization,
            'relationship_out': capability.applying_to.get_relationship_to(target_organization),
            'relationship_in': capability.applying_to.get_relationship_from(target_organization),
            'subtemplate': 'organization/capabilities/diplomacy_target.html',
        }
        return render(request, 'organization/capability.html', context)

    @transaction.atomic
    def post(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.DIPLOMACY)
        target_organization = get_object_or_404(Organization, id=target_organization_id)

        target_relationship = request.POST.get('target_relationship')

        if target_relationship in ("accept", "refuse"):
            if not target_organization.get_relationship_to(capability.applying_to).is_proposal():
                messages.error(request, "You cannot do that (1)", "danger")
                return redirect(reverse('organization:diplomacy_capability', kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id}))
            proposal = {
                'type': target_relationship,
                'target_organization_id': target_organization.id,
                'target_relationship': target_organization.get_relationship_to(capability.applying_to).desired_relationship
            }
        elif target_relationship == "take back":
            if not capability.applying_to.get_relationship_to(target_organization).is_proposal():
                messages.error(request, "You cannot do that (2)", "danger")
                return redirect(reverse('organization:diplomacy_capability', kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id}))
            proposal = {
                'type': target_relationship,
                'target_organization_id': target_organization.id,
                'target_relationship': capability.applying_to.get_relationship_to(target_organization).desired_relationship
            }
        else:
            if capability.applying_to.get_relationship_to(target_organization).is_proposal():
                messages.error(request, "You cannot do that", "danger")
                return redirect(reverse('organization:diplomacy_capability', kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id}))
            if target_relationship not in [choice[0] for choice in OrganizationRelationship.RELATIONSHIP_CHOICES]:
                messages.error(request, "You cannot do that (3)", "danger")
                return redirect(reverse('organization:diplomacy_capability', kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id}))
            proposal = {
                'type': 'propose',
                'target_organization_id': target_organization.id,
                'target_relationship': target_relationship
            }

        capability.create_proposal(request.hero, proposal)

        if capability.organization.decision_taking == Organization.DEMOCRATIC:
            messages.success(request, "A vote has been started regarding your action", "success")
        else:
            messages.success(request, "Done!", "success")
        return redirect(reverse(
            'organization:diplomacy_capability',
            kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id})
        )


class MilitaryStanceCapabilityView(View):
    def get(self, request, capability_id, target_organization_id):
        capability = get_object_or_404(Capability, id=capability_id, type=Capability.MILITARY_STANCE)
        target_organization = get_object_or_404(Organization, id=target_organization_id, violence_monopoly=True)
        regions = list(
            capability.applying_to.world.tile_set.exclude(type__in=(Tile.DEEPSEA, Tile.SHORE)).order_by('name')
        )
        for region in regions:
            region.stance = capability.applying_to.get_region_stance_to(target_organization, region)

        context = {
            'capability': capability,
            'target_organization': target_organization,
            'stance': capability.applying_to.get_default_stance_to(target_organization),
            'regions': regions,
            'subtemplate': 'organization/capabilities/military stance_target.html',
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
            region = get_object_or_404(Tile, id=request.POST['region_id'], world=capability.applying_to.world)
            if not region.is_on_ground():
                raise Http404()
            proposal['region_id'] = region.id

        capability.create_proposal(request.hero, proposal)

        if capability.organization.decision_taking == Organization.DEMOCRATIC:
            messages.success(request, "A vote has been started regarding your action", "success")
        else:
            messages.success(request, "Done!", "success")
        return redirect(reverse(
            'organization:military_stance_capability',
            kwargs={'capability_id': capability_id, 'target_organization_id': target_organization_id})
        )


class ProposalView(View):
    def check(self, request, proposal_id):
        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)
        if not proposal.capability.organization.character_is_member(request.hero):
            messages.error(request, "You cannot do that", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

    def get(self, request, proposal_id):
        check_result = self.check(request, proposal_id)
        if check_result is not None:
            return check_result

        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)
        proposal_content = json.loads(proposal.proposal_json)

        try:
            heros_vote = proposal.capabilityvote_set.get(voter=request.hero)
        except CapabilityVote.DoesNotExist:
            heros_vote = None

        context = {
            'proposal': proposal,
            'proposal_content': proposal_content,
            'heros_vote': heros_vote,
            'subtemplate': 'organization/proposals/{}.html'.format(proposal.capability.type),
        }

        if proposal.capability.type == Capability.POLICY_DOCUMENT:
            try:
                context['document'] = PolicyDocument.objects.get(id=proposal_content['document_id'])
            except PolicyDocument.DoesNotExist:
                context['document'] = None

        elif proposal.capability.type == Capability.BAN:
            context['character_to_ban'] = Character.objects.get(id=proposal_content['character_id'])

        elif proposal.capability.type == Capability.DIPLOMACY:
            context['target_organization'] = Organization.objects.get(id=proposal_content['target_organization_id'])
            context['target_relationship_html'] = OrganizationRelationship(relationship=proposal_content['target_relationship']).get_relationship_html()

        return render(request, 'organization/proposal.html', context)

    def post(self, request, proposal_id):
        check_result = self.check(request, proposal_id)
        if check_result is not None:
            return check_result

        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)

        if proposal.closed:
            messages.error(request, "Voting closed", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

        issued_vote = request.POST.get('vote')
        if issued_vote not in dict(CapabilityVote.VOTE_CHOICES).keys():
            messages.error(request, "Invalid vote", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))

        proposal.issue_vote(request.hero, issued_vote)

        messages.success(request, "Your vote has been issued.", "success")

        return redirect(proposal.get_absolute_url())
