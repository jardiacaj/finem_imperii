from django.test import TestCase
from django.urls.base import reverse

from battle.battle_init import initialize_from_conflict, start_battle
from battle.models import Battle
from organization.models import Organization
from world.initialization import initialize_unit
from world.models import Tile
from unit.models import WorldUnit


class TestBattleViews(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 5}),
            follow=True
        )
        initialize_unit(WorldUnit.objects.get(id=1))
        initialize_unit(WorldUnit.objects.get(id=2))
        initialize_unit(WorldUnit.objects.get(id=3))
        tile = Tile.objects.get(id=108)
        self.battle = Battle.objects.create(tile=tile, start_turn=0)
        initialize_from_conflict(
            self.battle,
            [
                [Organization.objects.get(id=105)],
                [Organization.objects.get(id=112)]
            ],
            tile
        )

    def test_info_view_when_not_started(self):
        response = self.client.get(reverse('battle:info', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

    def test_info_view_when_started(self):
        start_battle(self.battle)
        response = self.client.get(reverse('battle:info', kwargs={'battle_id': self.battle.id}))
        self.assertEqual(response.status_code, 200)

    def test_battlefield_view_when_not_started(self):
        response = self.client.get(reverse('battle:battlefield', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertRedirects(response, reverse('battle:info', kwargs={'battle_id': self.battle.id}))

    def test_battlefield_view_when_started(self):
        start_battle(self.battle)
        response = self.client.get(reverse('battle:battlefield', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_iframe_view_when_not_started(self):
        response = self.client.get(reverse('battle:battlefield_iframe', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_iframe_view_when_started(self):
        start_battle(self.battle)
        response = self.client.get(reverse('battle:battlefield_iframe', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_orders_view_when_not_started(self):
        response = self.client.get(reverse('battle:set_orders', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_orders_view_when_started(self):
        start_battle(self.battle)
        response = self.client.get(reverse('battle:set_orders', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_orders_view_when_not_participating(self):
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 3}),
            follow=True
        )
        response = self.client.get(reverse('battle:set_orders', kwargs={'battle_id': self.battle.id}), follow=True)
        self.assertEqual(response.status_code, 404)
