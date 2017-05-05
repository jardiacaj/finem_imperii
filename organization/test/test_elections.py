from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, CapabilityProposal


class TestElections(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.log_in_as(8)

        self.elect_capability = Capability.objects.get(
            organization__id=107,
            type=Capability.ELECT,
            applying_to_id=108
        )
        self.convoke_capability = Capability.objects.get(
            organization__id=107,
            type=Capability.CONVOKE_ELECTIONS,
            applying_to_id=108
        )
        self.candidacy_capability = Capability.objects.get(
            organization__id=107,
            type=Capability.CANDIDACY,
            applying_to_id=108
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
        # TODO incomplete test