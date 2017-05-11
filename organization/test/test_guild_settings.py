from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability
from world.models import Settlement


class TestGuildSetting(TestCase):

    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 7}),
            follow=True
        )

    def test_view(self):
        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.GUILDS,
            applying_to_id=105
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_change_setting(self):
        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.GUILDS,
            applying_to_id=105
        )

        response = self.client.post(
            reverse(
                'organization:guilds_capability',
                kwargs={'capability_id': capability.id}
            ),
            data={
                'option': 'prohibit guilds',
                'settlement_id': 1003,
            },
            follow=True
        )
        self.assertRedirects(response,
                             capability.organization.get_absolute_url())
        settlement = Settlement.objects.get(id=1003)
        self.assertEqual(settlement.guilds_setting, Settlement.GUILDS_PROHIBIT)
