from django.shortcuts import get_object_or_404, render
from django.views import View

from organization.models import PositionCandidacy, PositionElectionVote, \
    Capability
from world.models.events import TileEvent


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
