from django.test import TestCase
from django.urls.base import reverse

from organization.models.capability import Capability
from character.models import Character, CharacterEvent


class TestArrestWarrant(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        response = self.client.get(
            reverse('character:activate', kwargs={'char_id': 1}),
            follow=True
        )

    def test_warrant(self):
        capability = Capability.objects.get(
            organization_id=102,
            type=Capability.ARREST_WARRANT,
            applying_to_id=101
        )

        to_arrest = Character.objects.get(id=2)
        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "King")
        self.assertContains(response, "Kingdom Member")

        response = self.client.post(
            reverse('organization:arrest_warrant_capability', kwargs={
                'capability_id': capability.id
            }),
            data={'character_to_imprison_id': to_arrest.id},
            follow=True
        )
        self.assertRedirects(
            response, capability.organization.get_absolute_url())

        warrant = CharacterEvent.objects.get(
            character=to_arrest,
            active=True,
            organization_id=101,
            type=CharacterEvent.ARREST_WARRANT
        )

        response = self.client.post(
            reverse('organization:arrest_warrant_revoke_capability', kwargs={
                'capability_id': capability.id,
                'warrant_id': warrant.id
            }),
            data={},
            follow=True
        )
        self.assertRedirects(
            response, capability.organization.get_absolute_url())

        warrant.refresh_from_db()
        self.assertFalse(warrant.active)
