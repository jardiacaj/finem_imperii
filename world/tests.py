from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from organization.models import Organization
from world.models import World, Character


class TestHome(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)

    def test_activate_character(self):
        response = self.client.get(
            reverse('world:activate_character', kwargs={'char_id':1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('world:character_home'))


class TestCharacterCreation(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)

    def test_create_character_in_kingdom(self):
        response = self.client.post(
            reverse('world:create_character', kwargs={'world_id': 2}),
            data={
                'state_id': Organization.objects.get(name="Small Kingdom").id,
                'name': 'Rusbel',
                'surname': 'Gossett'
            },
            follow=True
        )

        new_character = Character.objects.get(name="Rusbel Gossett")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('world:activate_character', kwargs={'char_id': new_character.id})
        )
        self.assertEqual(response.redirect_chain[1][1], 302)
        self.assertEqual(response.redirect_chain[1][0], reverse('world:character_home'))


class TestTileView(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id':1}),
            follow=True
        )

    def test_view_region_in_wrong_world(self):
        for i in range(9):
            response = self.client.get(
                reverse('world:tile', kwargs={'tile_id': i}),
                follow=True
            )
            self.assertEqual(response.status_code, 404, i)

    def test_view_region_in_world2(self):
        for tile in World.objects.get(id=2).tile_set.all():
            response = self.client.get(
                reverse('world:tile', kwargs={'tile_id': tile.id}),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
