from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from world.models import World, Character


class TestTravel(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 1}),
            follow=True
        )

    def test_travel_view(self):
        response = self.client.get(reverse('world:travel'))
        self.assertEqual(response.status_code, 200)

    def test_travel_step2_view(self):
        response = self.client.get(
            reverse('world:travel', kwargs={'settlement_id': 1008}))
        self.assertEqual(response.status_code, 200)

    def test_travel_iframe_view(self):
        response = self.client.get(reverse('world:travel_iframe'))
        self.assertEqual(response.status_code, 200)

    def test_travel_iframe_view_with_destination(self):
        response = self.client.get(
            reverse('world:travel_iframe', kwargs={'settlement_id': 1001}))
        self.assertEqual(response.status_code, 200)

    def test_travel_in_tile(self):
        response = self.client.post(
            reverse('world:travel'),
            data={'target_settlement_id': 1008},
            follow=True
        )
        self.assertRedirects(response, reverse('world:travel'))

        character = Character.objects.get(id=1)
        self.assertEqual(character.location_id, 1008)
        self.assertEqual(character.hours_in_turn_left, 15*24 - 10)

    #TODO test_travel_to_other_tile