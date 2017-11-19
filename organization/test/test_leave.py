from django.test import TestCase
from django.urls.base import reverse

from organization.models import Organization
from character.models import Character


class TestLeaveOrganization(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )

    def test_leave_kingdom(self):
        organization = Organization.objects.get(name="Small Kingdom")
        character = Character.objects.get(id=1)

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        self.assertRedirects(response, organization.get_absolute_url())
        self.assertTrue(character.get_violence_monopoly().barbaric)
        self.assertIsNone(organization.leader.get_position_occupier())

    def test_king_step_out(self):
        organization = Organization.objects.get(name="Small King")
        character = Character.objects.get(id=1)

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        self.assertRedirects(response, organization.get_absolute_url())

        self.assertIsNone(organization.get_position_occupier(), None)

    def test_king_step_out_and_inherit(self):
        organization = Organization.objects.get(name="Small King")
        character = Character.objects.get(id=1)
        heir = Character.objects.get(id=2)

        organization.heir_first = heir
        organization.save()

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        self.assertRedirects(response, organization.get_absolute_url())

        self.assertEqual(organization.get_position_occupier(), heir)

    def test_king_step_out_and_inherit_second(self):
        organization = Organization.objects.get(name="Small King")
        character = Character.objects.get(id=1)
        heir = Character.objects.get(id=2)

        organization.heir_second = heir
        organization.save()

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        self.assertRedirects(response, organization.get_absolute_url())

        self.assertEqual(organization.get_position_occupier(), heir)

    def test_president_leave_democracy(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 4}),
            follow=True
        )
        organization = Organization.objects.get(name="Small Democracy")
        character = Character.objects.get(id=4)

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        organization.refresh_from_db()
        self.assertRedirects(response, organization.get_absolute_url())
        self.assertIsNone(organization.get_position_occupier())
        self.assertIsNotNone(organization.leader.current_election)
        self.assertEqual(organization.leader.current_election.turn, 6)

    def test_president_step_out(self):
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 4}),
            follow=True
        )
        organization = Organization.objects.get(name="Democracy leader")
        character = Character.objects.get(id=4)

        response = self.client.post(
            reverse(
                'organization:leave',
                kwargs={'organization_id': organization.id}
            ),
        )
        organization.refresh_from_db()
        self.assertRedirects(response, organization.get_absolute_url())
        self.assertIsNone(organization.get_position_occupier())
        self.assertIsNotNone(organization.current_election)
        self.assertEqual(organization.current_election.turn, 6)
