from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability
from character.models import Character


class TestViews(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        response = self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )

    def test_ban(self):
        capability = Capability.objects.get(
            organization_id=102,
            type=Capability.BAN,
            applying_to_id=101
        )

        to_ban = Character.objects.get(id=2)
        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "King")
        self.assertContains(response, "Kingdom Member")

        response = self.client.post(
            reverse('organization:banning_capability', kwargs={
                'capability_id': capability.id
            }),
            data={'character_to_ban_id': to_ban.id},
            follow=True
        )
        self.assertRedirects(
            response, capability.organization.get_absolute_url())

        vm = to_ban.get_violence_monopoly()
        self.assertEqual(vm.barbaric, True)
