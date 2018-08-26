from django.test import TestCase
from django.urls.base import reverse

from battle.models import Order
from organization.models.capability import Capability, CapabilityProposal
from world.models.events import TileEvent
from world.models.geography import World, Tile, Settlement
from character.models import Character
from unit.models import WorldUnit


class TestConquest(TestCase):

    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 7}),
            follow=True
        )

    def test_view(self):
        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.CONQUEST,
            applying_to_id=105
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        for tile in World.objects.get(id=2).tile_set.all():
            if tile.name in ("More mountains", Character.objects.get(id=7).location.tile.name):
                self.assertContains(response, tile.name)
            else:
                self.assertNotContains(response, tile.name)

    def test_start_conquest(self):
        tile = Tile.objects.get(name="More mountains")
        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.CONQUEST,
            applying_to_id=105
        )

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={
                'tile_to_conquest_id': tile.id,
            },
            follow=True
        )

        self.assertRedirects(response,
                             capability.organization.get_absolute_url())

        self.assertEqual(TileEvent.objects.count(), 1)
        event = TileEvent.objects.get(id=1)
        self.assertEqual(event.tile, tile)
        self.assertEqual(event.type, TileEvent.CONQUEST)
        self.assertEqual(event.organization.id, 105)
        self.assertEqual(event.counter, 0)
        self.assertEqual(event.start_turn, tile.world.current_turn)
        self.assertEqual(event.end_turn, None)
        self.assertEqual(event.active, True)

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': tile.id, },
        )

        self.assertEqual(response.status_code, 404)

    def test_start_and_stop_conquest(self):
        tile = Tile.objects.get(name="More mountains")
        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.CONQUEST,
            applying_to_id=105
        )

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': tile.id, },
            follow=True
        )

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': tile.id, 'stop': '1', },
            follow=True
        )
        self.assertRedirects(response,
                             capability.organization.get_absolute_url())
        self.assertEqual(TileEvent.objects.count(), 1)
        event = TileEvent.objects.get(id=1)
        self.assertEqual(event.tile, tile)
        self.assertEqual(event.type, TileEvent.CONQUEST)
        self.assertEqual(event.organization.id, 105)
        self.assertEqual(event.counter, 0)
        self.assertEqual(event.start_turn, tile.world.current_turn)
        self.assertEqual(event.end_turn, tile.world.current_turn)
        self.assertEqual(event.active, False)

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': tile.id, 'stop': '1', },
            follow=True
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={
                'tile_to_conquest_id': tile.id,
            },
            follow=True
        )

        self.assertRedirects(response,
                             capability.organization.get_absolute_url())

        self.assertEqual(TileEvent.objects.count(), 2)
        event = TileEvent.objects.get(id=2)
        self.assertEqual(event.tile, tile)
        self.assertEqual(event.type, TileEvent.CONQUEST)
        self.assertEqual(event.organization.id, 105)
        self.assertEqual(event.counter, 0)
        self.assertEqual(event.start_turn, tile.world.current_turn)
        self.assertEqual(event.end_turn, None)
        self.assertEqual(event.active, True)

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_proposal(self):
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 8}),
            follow=True
        )

        capability = Capability.objects.get(
            organization__id=107,
            type=Capability.CONQUEST,
            applying_to_id=107
        )
        settlement = Settlement.objects.get(id=1008)

        WorldUnit.objects.create(
            owner_character_id=8,
            world_id=2,
            location=settlement,
            name="conqueror",
            recruitment_type=WorldUnit.CONSCRIPTED,
            type=WorldUnit.LIGHT_INFANTRY,
            status=WorldUnit.STANDING,
            mobilization_status_since=0,
            current_status_since=0,
            battle_line=3,
            battle_side_pos=0,
            generation_size=30,
            default_battle_orders=Order.objects.create(what=''),
        )

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': settlement.tile.id, },
            follow=True
        )

        self.assertRedirects(response,
                             capability.organization.get_absolute_url())

        self.assertEqual(CapabilityProposal.objects.count(), 1)
        proposal = CapabilityProposal.objects.get(id=1)
        self.assertEqual(proposal.capability, capability)
        proposal_json = proposal.get_proposal_json_content()
        self.assertEqual(proposal_json['tile_id'], settlement.tile.id)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_proposal_fails_because_unit_is_not_mobilized(self):
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 8}),
            follow=True
        )

        capability = Capability.objects.get(
            organization__id=107,
            type=Capability.CONQUEST,
            applying_to_id=107
        )
        settlement = Settlement.objects.get(id=1008)

        WorldUnit.objects.create(
            owner_character_id=8,
            world_id=2,
            location=settlement,
            name="conqueror",
            recruitment_type=WorldUnit.CONSCRIPTED,
            type=WorldUnit.LIGHT_INFANTRY,
            status=WorldUnit.NOT_MOBILIZED,
            mobilization_status_since=0,
            current_status_since=0,
            battle_line=3,
            battle_side_pos=0,
            generation_size=30,
            default_battle_orders=Order.objects.create(what=''),
        )

        response = self.client.post(
            reverse('organization:conquest_capability', kwargs={'capability_id': capability.id}),
            data={'tile_to_conquest_id': settlement.tile.id, },
            follow=True
        )

        self.assertEqual(response.status_code, 404)
