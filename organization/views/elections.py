from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from decorators import inchar_required
from messaging import shortcuts
from organization.models.capability import Capability
from organization.models.election import PositionElection, PositionCandidacy, \
    PositionElectionVote
from organization.models.organization import Organization
from organization.views.proposal import capability_success
from organization.views.decorator import capability_required_decorator


@require_POST
@capability_required_decorator
def elect_capability_view(request, capability_id):
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
def election_convoke_capability_view(request, capability_id):
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
def present_candidacy_capability_view(request, capability_id):
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