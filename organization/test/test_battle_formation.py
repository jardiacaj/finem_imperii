from django.test import TestCase
from django.urls.base import reverse

from battle.models import BattleFormation
from organization.models.capability import Capability, CapabilityProposal


class TestBattleFormation(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 1}),
            follow=True
        )

    def test_view(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.BATTLE_FORMATION,
            applying_to_id=101
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('organization:battle_formation_capability', kwargs={
                'capability_id': capability.id
            })
        )
        self.assertEqual(response.status_code, 405)

    def test_set_formation(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.BATTLE_FORMATION,
            applying_to_id=101
        )

        response = self.client.post(
            reverse('organization:battle_formation_capability', kwargs={'capability_id': capability.id}),
            data={
                'new_formation': 'line',
                'line_depth': 2,
                'line_spacing': 3
            },
            follow=True
        )

        self.assertRedirects(response,
                             capability.organization.get_absolute_url())

        self.assertEqual(BattleFormation.objects.count(), 1)
        self.assertTrue(BattleFormation.objects.filter(battle=None, organization_id=101).exists())
        formation = BattleFormation.objects.get(battle=None, organization_id=101)
        self.assertEqual(formation.formation, 'line')
        self.assertEqual(formation.spacing, 3)
        self.assertEqual(formation.element_size, 2)

    def test_proposal_view(self):
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 4}),
            follow=True
        )

        capability = Capability.objects.get(
            organization__id=107,
            type=Capability.BATTLE_FORMATION,
            applying_to_id=107
        )

        response = self.client.post(
            reverse('organization:battle_formation_capability', kwargs={'capability_id': capability.id}),
            data={
                'new_formation': 'line',
                'line_depth': 2,
                'line_spacing': 3
            },
            follow=True
        )

        self.assertRedirects(response,
                             capability.organization.get_absolute_url())

        self.assertEqual(CapabilityProposal.objects.count(), 1)
        proposal = CapabilityProposal.objects.get(id=1)
        self.assertEqual(proposal.capability, capability)
        proposal_json = proposal.get_proposal_json_content()
        self.assertEqual(proposal_json['formation'], 'line')
        self.assertEqual(proposal_json['element_size'], 2)
        self.assertEqual(proposal_json['spacing'], 3)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)
