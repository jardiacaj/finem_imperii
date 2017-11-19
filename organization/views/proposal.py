import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from base.utils import redirect_back
from character.models import Character
from organization.models.relationship import OrganizationRelationship
from organization.models.document import PolicyDocument
from organization.models.capability import Capability, CapabilityProposal, \
    CapabilityVote
from organization.models.organization import Organization
from world.models.geography import Tile, Settlement


def policy_proposal_context(proposal_content, context):
    try:
        context['document'] = PolicyDocument.objects.get(
            id=proposal_content['document_id'])
    except PolicyDocument.DoesNotExist:
        context['document'] = None


def ban_proposal_context(proposal_content, context):
    context['character_to_ban'] = Character.objects.get(
        id=proposal_content['character_id'])


def diplomacy_proposal_context(proposal_content, context):
    context['target_organization'] = Organization.objects.get(
        id=proposal_content['target_organization_id'])
    context['target_relationship_html'] = OrganizationRelationship(
        relationship=proposal_content['target_relationship']
    ).get_relationship_html()


def conquest_proposal_context(proposal_content, context):
    context['target_tile'] = Tile.objects.get(
        id=proposal_content['tile_id'])


def guilds_proposal_context(proposal_content, context):
    context['settlement'] = Settlement.objects.get(
        id=proposal_content['settlement_id']
    )


def heir_proposal_context(proposal_content, context):
    context['first_heir'] = Character.objects.get(
        id=proposal_content['first_heir'])
    context['second_heir'] = (
        None if proposal_content['second_heir'] == 0 else
        Character.objects.get(id=proposal_content['second_heir'])
    )


class ProposalView(View):
    context_decorators = {
        Capability.POLICY_DOCUMENT: policy_proposal_context,
        Capability.BAN: ban_proposal_context,
        Capability.DIPLOMACY: diplomacy_proposal_context,
        Capability.CONQUEST: conquest_proposal_context,
        Capability.GUILDS: guilds_proposal_context,
        Capability.HEIR: heir_proposal_context,
    }

    def check(self, request, proposal_id):
        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)
        if not proposal.capability.organization.character_is_member(
                request.hero):
            messages.error(request, "You cannot do that", "danger")
            return redirect_back(request, reverse('character:character_home'),
                                 error_message="You cannot do that")

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

        if proposal.capability.type in self.context_decorators.keys():
            self.context_decorators[proposal.capability.type](
                proposal_content, context
            )

        return render(request, 'organization/proposal.html', context)

    def post(self, request, proposal_id):
        check_result = self.check(request, proposal_id)
        if check_result is not None:
            return check_result

        proposal = get_object_or_404(CapabilityProposal, id=proposal_id)

        if proposal.closed:
            return redirect_back(request, reverse('character:character_home'),
                                 error_message="Voting closed")

        issued_vote = request.POST.get('vote')
        if issued_vote not in dict(CapabilityVote.VOTE_CHOICES).keys():
            return redirect_back(request, reverse('character:character_home'),
                                 error_message="Invalid vote")

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
