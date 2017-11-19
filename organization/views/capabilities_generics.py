import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from character.models import Character
from organization.models import Capability, PositionCandidacy, \
    PositionElectionVote, CapabilityProposal, CapabilityVote, PolicyDocument, \
    Organization, OrganizationRelationship
from world.models.events import TileEvent
from world.models.geography import Tile, Settlement


def candidacy_capability_context(request, capability, context):
    context['heros_candidacy'] = None
    if capability.applying_to.current_election:
        try:
            context['heros_candidacy'] = capability.applying_to. \
                current_election.positioncandidacy_set. \
                get(candidate=request.hero)
        except PositionCandidacy.DoesNotExist:
            pass


def elect_capability_context(request, capability, context):
    context['heros_vote'] = None
    if capability.applying_to.current_election:
        try:
            context['heros_vote'] = capability.applying_to.current_election. \
                positionelectionvote_set.get(voter=request.hero)
        except PositionElectionVote.DoesNotExist:
            pass


def diplomacy_capability_context(request, capability, context):
    if capability.applying_to.violence_monopoly:
        context['states'] = []
        for state in capability.applying_to.world.get_violence_monopolies():
            if state == capability.applying_to:
                continue
            state.relationship_out = state.get_relationship_from(
                capability.applying_to
            )
            state.relationship_in = state.get_relationship_to(
                capability.applying_to
            )
            context['states'].append(state)


def military_stance_capability_context(request, capability, context):
    if capability.applying_to.violence_monopoly:
        context['states'] = []
        for state in capability.applying_to.world.get_violence_monopolies():
            if state == capability.applying_to:
                continue
            state.default_stance = capability.applying_to. \
                get_default_stance_to(state)
            state.region_stances = capability.applying_to. \
                get_region_stances_to(state)
            context['states'].append(state)


def conquest_capability_context(request, capability, context):
    if capability.applying_to.violence_monopoly:
        context['conquestable_tiles'] = capability.applying_to. \
            conquestable_tiles()
        context['conquests_in_progress'] = TileEvent.objects.filter(
            organization=capability.applying_to,
            type=TileEvent.CONQUEST,
            end_turn=None
        )


class CapabilityView(View):
    context_decorators = {
        Capability.CANDIDACY: candidacy_capability_context,
        Capability.ELECT: elect_capability_context,
        Capability.DIPLOMACY: diplomacy_capability_context,
        Capability.MILITARY_STANCE: military_stance_capability_context,
        Capability.CONQUEST: conquest_capability_context,
    }

    def get(self, request, capability_id):
        capability = get_object_or_404(Capability, id=capability_id)

        context = {
            'capability': capability,
            'subtemplate': 'organization/capabilities/{}.html'.format(
                capability.type
            ),
        }

        if capability.type in self.context_decorators.keys():
            self.context_decorators[capability.type](
                request, capability, context
            )

        return render(request, 'organization/capability.html', context)


class ProposalView(View):
    def check(self, request, proposal_id):
        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)
        if not proposal.capability.organization.character_is_member(
                request.hero):
            messages.error(request, "You cannot do that", "danger")
            return redirect(
                request.META.get(
                    'HTTP_REFERER',
                    reverse('character:character_home')
                )
            )

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
            'subtemplate': 'organization/proposals/{}.html'.format(
                proposal.capability.type),
        }

        if proposal.capability.type == Capability.POLICY_DOCUMENT:
            try:
                context['document'] = PolicyDocument.objects.get(
                    id=proposal_content['document_id'])
            except PolicyDocument.DoesNotExist:
                context['document'] = None

        elif proposal.capability.type == Capability.BAN:
            context['character_to_ban'] = Character.objects.get(
                id=proposal_content['character_id'])

        elif proposal.capability.type == Capability.DIPLOMACY:
            context['target_organization'] = Organization.objects.get(
                id=proposal_content['target_organization_id'])
            context['target_relationship_html'] = OrganizationRelationship(
                relationship=proposal_content['target_relationship']
            ).get_relationship_html()

        elif proposal.capability.type == Capability.CONQUEST:
            context['target_tile'] = Tile.objects.get(
                id=proposal_content['tile_id'])

        elif proposal.capability.type == Capability.GUILDS:
            context['settlement'] = Settlement.objects.get(
                id=proposal_content['settlement_id']
            )

        elif proposal.capability.type == Capability.HEIR:
            context['first_heir'] = Character.objects.get(
                id=proposal_content['first_heir'])
            context['second_heir'] = (
                None if proposal_content['second_heir'] == 0 else
                Character.objects.get(id=proposal_content['second_heir'])
            )

        return render(request, 'organization/proposal.html', context)

    def post(self, request, proposal_id):
        check_result = self.check(request, proposal_id)
        if check_result is not None:
            return check_result

        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)

        if proposal.closed:
            messages.error(request, "Voting closed", "danger")
            return redirect(
                request.META.get(
                    'HTTP_REFERER',
                    reverse('character:character_home')
                )
            )

        issued_vote = request.POST.get('vote')
        if issued_vote not in dict(CapabilityVote.VOTE_CHOICES).keys():
            messages.error(request, "Invalid vote", "danger")
            return redirect(
                request.META.get(
                    'HTTP_REFERER',
                    reverse('character:character_home')
                )
            )

        proposal.issue_vote(request.hero, issued_vote)

        messages.success(request, "Your vote has been issued.", "success")

        return redirect(proposal.get_absolute_url())


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
