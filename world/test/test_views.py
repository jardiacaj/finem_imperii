from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

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

    def test_view_region_iframe(self):
        for tile in World.objects.get(id=2).tile_set.all():
            response = self.client.get(
                reverse('world:tile_iframe', kwargs={'tile_id': tile.id}),
                follow=True
            )
            self.assertEqual(response.status_code, 200)


class TestWorldView(TestCase):
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

    def test_view_world(self):
        world = World.objects.get(id=2)
        response = self.client.get(world.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_view_character(self):
        character = Character.objects.get(id=2)
        response = self.client.get(character.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_view_world_iframe(self):
        response = self.client.get(reverse('world:world_iframe', kwargs={'world_id': 2}))
        self.assertEqual(response.status_code, 200)

    def test_view_minimap_iframe(self):
        response = self.client.get(reverse('world:minimap'))
        self.assertEqual(response.status_code, 200)
