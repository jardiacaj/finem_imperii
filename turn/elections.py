from messaging import shortcuts
from organization.models.election import PositionElection
from organization.models.organization import Organization
from world.models.geography import World


def worldwide_do_elections(world: World):
    for election in PositionElection.objects.filter(
        position__world=world,
        turn=world.current_turn
    ):
        election.resolve()

    for organization in world.organization_set.filter(
        position_type=Organization.ELECTED
    ):
        if not organization.current_election:
            if not organization.last_election:
                turns_to_next_election = 6
            else:
                turns_since_last_election = world.current_turn - organization.last_election.turn
                turns_to_next_election = organization.election_period_months - turns_since_last_election
            organization.convoke_elections(turns_to_next_election)
        elif organization.current_election.turn - organization.world.current_turn == 3:
            message = shortcuts.create_message(
                'messaging/messages/elections_soon.html',
                world,
                'elections',
                {'election': organization.current_election},
                link=organization.current_election.get_absolute_url()
            )
