from django.contrib import auth
from django.test import TestCase
from django.urls.base import reverse

from world.models import World, InventoryItem
from character.models import Character


class TestInventory(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 1}),
            follow=True
        )

    def test_view_inventory(self):
        character = Character.objects.get(id=1)
        granary_bushels_object = character.location.get_default_granary()\
            .get_public_bushels_object()
        granary_bushels_object.quantity = 100
        granary_bushels_object.save()

        response = self.client.get(reverse('character:inventory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Take grain from granary")

    def test_take_grain(self):
        character = Character.objects.get(id=1)
        bushels_object = character.location.get_default_granary()\
            .get_public_bushels_object()
        bushels_object.quantity = 100
        bushels_object.save()

        response = self.client.post(
            reverse('character:inventory'),
            data={
                'action': 'load',
                'bushels': 99
            }
        )
        self.assertRedirects(response, reverse('character:inventory'))

        bushels_object.refresh_from_db()
        self.assertEqual(bushels_object.quantity, 1)

        inv_bush = character.inventory_object(InventoryItem.GRAIN)
        self.assertEqual(inv_bush.quantity, 99)

        character.refresh_from_db()
        self.assertEqual(character.hours_in_turn_left, 15*24 - 100/2)

    def test_take_grain_with_carts(self):
        character = Character.objects.get(id=1)
        bushels_object = character.location.get_default_granary()\
            .get_public_bushels_object()
        bushels_object.quantity = 1000
        bushels_object.save()

        character.profile = Character.TRADER
        character.save()

        InventoryItem.objects.create(
            type=InventoryItem.CART,
            quantity=10,
            owner_character=character
        )

        inv_cart = character.inventory_object(InventoryItem.CART)
        self.assertEqual(inv_cart.quantity, 10)

        response = self.client.post(
            reverse('character:inventory'),
            data={
                'action': 'load',
                'bushels': 1000
            }
        )
        self.assertRedirects(response, reverse('character:inventory'))

        inv_bush = character.inventory_object(InventoryItem.GRAIN)
        self.assertEqual(inv_bush.quantity, 1000)

        bushels_object.refresh_from_db()
        self.assertEqual(bushels_object.quantity, 0)

        character.refresh_from_db()
        self.assertEqual(character.hours_in_turn_left, 15*24 - 1000/4)

    def test_unload_grain(self):
        character = Character.objects.get(id=1)
        character_bushels_object = InventoryItem.objects.create(
            type=InventoryItem.GRAIN,
            quantity=100,
            owner_character=character
        )

        response = self.client.post(
            reverse('character:inventory'),
            data={
                'action': 'unload',
                'bushels': 99
            }
        )
        self.assertRedirects(response, reverse('character:inventory'))

        character_bushels_object.refresh_from_db()
        self.assertEqual(character_bushels_object.quantity, 1)

        granary_bushels_object = character.location.get_default_granary()\
            .get_public_bushels_object()
        self.assertEqual(granary_bushels_object.quantity, 99)

        character.refresh_from_db()
        self.assertEqual(character.hours_in_turn_left, 15*24 - 100/2)
