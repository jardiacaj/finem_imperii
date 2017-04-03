from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, MilitaryStance


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
            reverse('world:activate_character', kwargs={'char_id':1}),
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
