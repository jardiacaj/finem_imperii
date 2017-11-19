from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability


class TestCapabilities(TestCase):
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

    def test_disallowed_capability_get(self):
        capability = Capability.objects.get(
            organization__id=105,
            type=Capability.BAN,
            applying_to_id=105
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertRedirects(response, reverse('character:character_home'))

    def test_disallowed_capability_post(self):
        capability = Capability.objects.get(
            organization__id=105,
            type=Capability.BAN,
            applying_to_id=105
        )

        response = self.client.post(capability.get_absolute_url())
        self.assertRedirects(response, reverse('character:character_home'))
