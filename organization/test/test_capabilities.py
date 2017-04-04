from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from battle.models import BattleFormation
from organization.models import Capability, MilitaryStance, CapabilityProposal


class TestMilitaryOrders(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        response = self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('world:character_home'))

    def test_view(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.MILITARY_STANCE,
            applying_to_id=101
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            })
        )
        self.assertEqual(response.status_code, 200)

    def test_view_wrong_target(self):
        capability = Capability.objects.get(organization__id=102, type=Capability.MILITARY_STANCE, applying_to_id=101)
        response = self.client.get(
            reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 102
            })
        )
        self.assertEqual(response.status_code, 404)

    def test_post_new_general_stance(self):
        capability = Capability.objects.get(organization__id=102, type=Capability.MILITARY_STANCE, applying_to_id=101)
        response = self.client.post(
            reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'new_stance': MilitaryStance.AGGRESSIVE},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }))

        stance = MilitaryStance.objects.get(from_organization_id=101, to_organization_id=105, region=None)
        self.assertEqual(stance.get_stance(), MilitaryStance.AGGRESSIVE)

    def test_post_new_region_stance(self):
        capability = Capability.objects.get(organization__id=102, type=Capability.MILITARY_STANCE, applying_to_id=101)
        response = self.client.post(
            reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'new_stance': MilitaryStance.AGGRESSIVE, 'region_id': 102},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }))

        stance = MilitaryStance.objects.get(from_organization_id=101, to_organization_id=105, region_id=102)
        self.assertEqual(stance.get_stance(), MilitaryStance.AGGRESSIVE)

        stance = MilitaryStance.objects.get(from_organization_id=101, to_organization_id=105, region_id=None)
        self.assertEqual(stance.get_stance(), MilitaryStance.DEFENSIVE)

    def test_post_ocean_region_stance(self):
        capability = Capability.objects.get(organization__id=102, type=Capability.MILITARY_STANCE, applying_to_id=101)
        response = self.client.post(
            reverse('organization:military_stance_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'new_stance': MilitaryStance.AGGRESSIVE, 'region_id': 101},
            follow=True
        )
        self.assertEqual(response.status_code, 404)


class TestBattleFormation(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 1}),
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

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(BattleFormation.objects.count(), 1)
        self.assertTrue(BattleFormation.objects.filter(battle=None, organization_id=101).exists())
        formation = BattleFormation.objects.get(battle=None, organization_id=101)
        self.assertEqual(formation.formation, 'line')
        self.assertEqual(formation.spacing, 3)
        self.assertEqual(formation.element_size, 2)

    def test_proposal_view(self):
        self.client.get(
            reverse('world:activate_character', kwargs={'char_id': 4}),
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

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(CapabilityProposal.objects.count(), 1)
        proposal = CapabilityProposal.objects.get(id=1)
        self.assertEqual(proposal.capability, capability)
        proposal_json = proposal.get_proposal_json_content()
        self.assertEqual(proposal_json['formation'], 'line')
        self.assertEqual(proposal_json['element_size'], 2)
        self.assertEqual(proposal_json['spacing'], 3)

        response = self.client.get(proposal.get_absolute_url())
        self.assertEqual(response.status_code, 200)
