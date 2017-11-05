from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, CapabilityProposal, Organization, \
    PositionElection, PositionCandidacy, CapabilityVote, PositionElectionVote


class TestElections(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.democracy_member_id = 8
        self.democracy_leader_id = 4
        self.democracy = Organization.objects.get(id=107)
        self.president = Organization.objects.get(id=108)

        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.log_in_as(self.democracy_member_id)

        self.elect_capability = Capability.objects.get(
            organization=self.democracy,
            type=Capability.ELECT,
            applying_to=self.president
        )
        self.convoke_capability = Capability.objects.get(
            organization=self.democracy,
            type=Capability.CONVOKE_ELECTIONS,
            applying_to=self.president
        )
        self.candidacy_capability = Capability.objects.get(
            organization=self.democracy,
            type=Capability.CANDIDACY,
            applying_to=self.president
        )

    def log_in_as(self, char_id):
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': char_id}),
            follow=True
        )

    def test_elect_view(self):
        response = self.client.get(self.elect_capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_convoke_view(self):
        response = self.client.get(self.convoke_capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_candidacy_view(self):
        response = self.client.get(self.candidacy_capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_convoke_elections(self):
        response = self.client.post(
            reverse(
                'organization:election_convoke_capability',
                kwargs={'capability_id': self.convoke_capability.id}
            ),
            data={'months_to_election': 7},
            follow=True
        )
        self.assertRedirects(
            response,
            self.convoke_capability.organization.get_absolute_url()
        )

        self.assertEqual(CapabilityProposal.objects.count(), 1)
        proposal = CapabilityProposal.objects.get(id=1)
        self.assertEqual(proposal.capability, self.convoke_capability)
        self.assertEqual(
            proposal.proposing_character_id, self.democracy_member_id)
        self.assertEqual(proposal.executed, False)
        self.assertEqual(proposal.closed, False)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.log_in_as(self.democracy_leader_id)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            proposal.get_absolute_url(),
            data={'vote': 'yea'},
            follow=True
        )

        self.assertRedirects(response, proposal.get_absolute_url())

        proposal.refresh_from_db()
        self.assertEqual(proposal.executed, True)
        self.assertEqual(proposal.closed, True)

        self.president.refresh_from_db()
        election = self.president.current_election
        self.assertIsNotNone(election)
        self.assertEqual(election.position, self.president)
        self.assertEqual(election.turn, 7)
        self.assertEqual(election.closed, False)
        self.assertEqual(election.winner, None)

        self.assertEqual(PositionCandidacy.objects.exists(), 1)
        candidacy = PositionCandidacy.objects.get(id=1)
        self.assertEqual(candidacy.election, self.president.current_election)
        self.assertEqual(candidacy.candidate_id, self.democracy_leader_id)
        self.assertEqual(candidacy.description, 'Automatic candidacy for incumbent character.')
        self.assertEqual(candidacy.retired, False)

        response = self.client.get(
            self.president.current_election.get_absolute_url()
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, candidacy.description)

    def test_present_candidacy(self):
        self.president.current_election = PositionElection.objects.create(
            position=self.president,
            turn=12,
            closed=False,
            winner=None
        )
        self.president.save()

        response = self.client.post(
            reverse(
                'organization:candidacy_capability',
                kwargs={'capability_id': self.candidacy_capability.id}
            ),
            data={'description': 'foobar'},
            follow=True
        )
        self.assertRedirects(
            response,
            self.candidacy_capability.get_absolute_url()
        )

        self.assertEqual(PositionCandidacy.objects.exists(), 1)
        candidacy = PositionCandidacy.objects.get(id=1)
        self.assertEqual(candidacy.election, self.president.current_election)
        self.assertEqual(candidacy.candidate_id, self.democracy_member_id)
        self.assertEqual(candidacy.description, 'foobar')
        self.assertEqual(candidacy.retired, False)

        self.assertEqual(PositionElectionVote.objects.count(), 0)

        response = self.client.get(
            self.president.current_election.get_absolute_url()
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'foobar')

    def test_vote(self):
        self.president.current_election = PositionElection.objects.create(
            position=self.president,
            turn=12,
            closed=False,
            winner=None
        )
        self.president.save()
        candidacy = PositionCandidacy.objects.create(
            election=self.president.current_election,
            candidate_id=self.democracy_member_id,
            description='foobar',
            retired=False
        )

        response = self.client.get(
            self.president.current_election.get_absolute_url()
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'foobar')

        response = self.client.get(self.elect_capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'foobar')

        response = self.client.post(
            reverse(
                'organization:elect_capability',
                kwargs={'capability_id': self.elect_capability.id}
            ),
            data={'candidacy_id': candidacy.id},
            follow=True
        )
        self.assertRedirects(
            response, self.elect_capability.get_absolute_url())

        self.assertEqual(PositionElectionVote.objects.count(), 1)
        vote = PositionElectionVote.objects.get(id=1)
        self.assertEqual(vote.election, self.president.current_election)
        self.assertEqual(vote.voter_id, self.democracy_member_id)
        self.assertEqual(vote.candidacy, candidacy)

    def test_pass_election(self):
        election = PositionElection.objects.create(
            position=self.president,
            turn=12,
            closed=False,
            winner=None
        )
        self.president.current_election = election
        self.president.save()
        candidacy = PositionCandidacy.objects.create(
            election=election,
            candidate_id=self.democracy_member_id,
            description='foobar',
            retired=False
        )
        vote = PositionElectionVote.objects.create(
            election=election,
            voter_id=self.democracy_member_id,
            candidacy=candidacy
        )

        election.resolve()
        election.refresh_from_db()
        self.assertEqual(election.closed, True)
        self.assertEqual(election.winner, candidacy)

        self.president.refresh_from_db()
        self.assertEqual(
            self.president.get_position_occupier().id,
            self.democracy_member_id
        )
