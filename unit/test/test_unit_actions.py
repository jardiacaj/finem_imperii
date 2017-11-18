from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from organization.models import Organization
from world.initialization import initialize_unit
from world.models import TileEvent, Tile, Character
from unit.models import WorldUnit


class TestUnitActions(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 6}),
            follow=True
        )

        self.not_my_unit = WorldUnit.objects.get(id=1)
        self.my_unit = WorldUnit.objects.get(id=2)
        initialize_unit(self.my_unit)
        initialize_unit(self.not_my_unit)

    def test_disband(self):
        response = self.client.post(
            reverse('unit:unit_disband', kwargs={'unit_id': 2})
        )

        self.assertRedirects(
            response,
            reverse('world:character_home')
        )
        self.my_unit.refresh_from_db()
        self.assertIsNone(self.my_unit.location)
        self.assertIsNone(self.my_unit.world)
        self.assertIsNone(self.my_unit.owner_character)

    def test_support_conquest(self):
        tile = Tile.objects.get(name="More mountains")
        conqueror = Organization.objects.get(id=105)

        tile_event = TileEvent.objects.create(
            tile=tile,
            type=TileEvent.CONQUEST,
            organization=conqueror,
            counter=0,
            start_turn=0
        )

        response = self.client.post(
            reverse('unit:unit_conquest_action', kwargs={'unit_id': 2}),
            data={
                'action': 'support',
                'conqueror_id': conqueror.id,
                'hours': 30
            }
        )

        self.assertRedirects(response, self.my_unit.get_absolute_url())

        tile_event.refresh_from_db()
        self.assertEqual(tile_event.counter, 2)  # 30*30 // (15*24)

        character = Character.objects.get(id=6)
        self.assertEqual(character.hours_in_turn_left, (15*24) - 30)

    def test_counter_conquest(self):
        tile = Tile.objects.get(name="More mountains")
        conqueror = Organization.objects.get(id=105)

        tile_event = TileEvent.objects.create(
            tile=tile,
            type=TileEvent.CONQUEST,
            organization=conqueror,
            counter=10,
            start_turn=0
        )

        response = self.client.post(
            reverse('unit:unit_conquest_action', kwargs={'unit_id': 2}),
            data={
                'action': 'counter',
                'conqueror_id': conqueror.id,
                'hours': 30
            }
        )

        self.assertRedirects(response, self.my_unit.get_absolute_url())

        tile_event.refresh_from_db()
        self.assertEqual(tile_event.counter, 8)  # 30*30 // (15*24)

        character = Character.objects.get(id=6)
        self.assertEqual(character.hours_in_turn_left, (15*24) - 30)
