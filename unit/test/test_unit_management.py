from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from battle.models import Order
from world.initialization import initialize_unit
from world.models import World
from unit.models import WorldUnit
from world.turn import pass_turn


class TestUnitManagement(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 5}),
            follow=True
        )

        self.my_unit = WorldUnit.objects.get(id=1)
        self.not_my_unit = WorldUnit.objects.get(id=2)
        initialize_unit(self.my_unit)
        initialize_unit(self.not_my_unit)

    def test_unit_rename(self):
        response = self.client.post(
            reverse('unit:rename', kwargs={'unit_id': self.my_unit.id}),
            data={'name': "My new name"},
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.name, "My new name")

    def test_unit_rename_denied(self):
        response = self.client.post(
            reverse('unit:rename', kwargs={'unit_id': self.not_my_unit.id}),
            data={'name': "My new name"}
        )
        self.assertEqual(response.status_code, 404)
        self.not_my_unit.refresh_from_db()
        self.assertNotEqual(self.not_my_unit.name, "My new name")

    def test_unit_change_settings(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_line': 1,
                'battle_side_pos': 2
            },
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.battle_line, 1)
        self.assertEqual(self.my_unit.battle_side_pos, 2)

    def test_unit_change_settings_frontest_line(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_line': 0,
                'battle_side_pos': 2
            },
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.battle_line, 0)
        self.assertEqual(self.my_unit.battle_side_pos, 2)

    def test_unit_change_settings_rearest_line(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_line': 0,
                'battle_side_pos': 4
            },
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.battle_line, 0)
        self.assertEqual(self.my_unit.battle_side_pos, 4)

    def test_unit_change_settings_minus_one_line(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_line': -1,
                'battle_side_pos': 2
            },
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_unit_change_settings_line_five(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_line': 5,
                'battle_side_pos': 2
            },
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_unit_change_orders(self):
        response = self.client.post(
            reverse('unit:battle_orders', kwargs={'unit_id': self.my_unit.id}),
            data={
                'battle_orders': 'flee'
            },
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.default_battle_orders.what, Order.FLEE)

    def test_unit_change_settings_denied(self):
        response = self.client.post(
            reverse('unit:battle_settings', kwargs={'unit_id': self.not_my_unit.id}),
            data={
                'battle_line': 1,
                'battle_side_pos': 2
            }
        )
        self.assertEqual(response.status_code, 404)
        self.not_my_unit.refresh_from_db()
        self.assertNotEqual(self.not_my_unit.battle_line, 1)
        self.assertNotEqual(self.not_my_unit.battle_side_pos, 2)

    def test_unit_set_status(self):
        self.assertEqual(self.my_unit.status, WorldUnit.FOLLOWING)
        response = self.client.post(
            reverse('unit:status_change', kwargs={'unit_id': self.my_unit.id, 'new_status': WorldUnit.STANDING}),
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.status, WorldUnit.STANDING)

    def test_unit_set_status_denied(self):
        self.assertEqual(self.not_my_unit.status, WorldUnit.FOLLOWING)
        response = self.client.post(
            reverse('unit:status_change', kwargs={'unit_id': self.not_my_unit.id, 'new_status': WorldUnit.STANDING}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.not_my_unit.refresh_from_db()
        self.assertEqual(self.not_my_unit.status, WorldUnit.FOLLOWING)

    def test_unit_set_status_too_soon(self):
        self.assertEqual(self.my_unit.status, WorldUnit.FOLLOWING)
        response = self.client.post(
            reverse('unit:status_change', kwargs={'unit_id': self.my_unit.id, 'new_status': WorldUnit.NOT_MOBILIZED}),
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.status, WorldUnit.FOLLOWING)

    def test_unit_set_status_in_battle(self):
        self.assertEqual(self.my_unit.status, WorldUnit.FOLLOWING)
        pass_turn(self.my_unit.world)
        response = self.client.post(
            reverse('unit:status_change', kwargs={'unit_id': self.my_unit.id, 'new_status': WorldUnit.NOT_MOBILIZED}),
            follow=True
        )
        self.assertRedirects(response, self.my_unit.get_absolute_url())
        self.my_unit.refresh_from_db()
        self.assertEqual(self.my_unit.status, WorldUnit.FOLLOWING)
