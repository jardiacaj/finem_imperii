from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, CapabilityProposal
from world.models import Settlement


class TestSetHeir(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )

    def test_view(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.HEIR,
            applying_to_id=102
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_set_heir(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.HEIR,
            applying_to_id=102
        )

        response = self.client.post(
            reverse(
                'organization:heir_capability',
                kwargs={'capability_id': capability.id}
            ),
            data={
                'first_heir': '2',
                'second_heir': '0',
            },
            follow=True
        )
        self.assertRedirects(response,
                             capability.organization.get_absolute_url())
        capability.applying_to.refresh_from_db()
        self.assertEqual(capability.applying_to.heir_first.id, 2)
        self.assertEqual(capability.applying_to.heir_second, None)

    def test_set_both_heirs(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.HEIR,
            applying_to_id=102
        )

        response = self.client.post(
            reverse(
                'organization:heir_capability',
                kwargs={'capability_id': capability.id}
            ),
            data={
                'first_heir': '2',
                'second_heir': '2',
            },
            follow=True
        )
        self.assertRedirects(response,
                             capability.organization.get_absolute_url())
        capability.applying_to.refresh_from_db()
        self.assertEqual(capability.applying_to.heir_first.id, 2)
        self.assertEqual(capability.applying_to.heir_second.id, 2)

    def test_proposal(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 6}),
            follow=True
        )
        capability = Capability.objects.get(
            organization__id=105,
            type=Capability.HEIR,
            applying_to_id=106
        )

        response = self.client.post(
            reverse(
                'organization:heir_capability',
                kwargs={'capability_id': capability.id}
            ),
            data={
                'first_heir': '6',
                'second_heir': '0',
            },
            follow=True
        )
        self.assertRedirects(response,
                             capability.organization.get_absolute_url())
        capability.applying_to.refresh_from_db()
        self.assertEqual(capability.applying_to.heir_first, None)
        self.assertEqual(capability.applying_to.heir_second, None)

        proposal = CapabilityProposal.objects.get(id=1)
        self.assertEqual(proposal.capability, capability)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)
