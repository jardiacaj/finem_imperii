from django.contrib import auth
from django.test import TestCase
from django.urls.base import reverse

from world.models import World, Character


class TestInventory(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 1}),
            follow=True
        )

    def test_view_inventory(self):
        response = self.client.get(reverse('world:inventory'))
        self.assertEqual(response.status_code, 200)
