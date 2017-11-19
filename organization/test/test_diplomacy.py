from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, Organization, \
    OrganizationRelationship


class TestDiplomacy(TestCase):
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
            type=Capability.DIPLOMACY,
            applying_to_id=101
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            })
        )
        self.assertEqual(response.status_code, 200)

    def test_no_diplomacy_with_barbarians(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.DIPLOMACY,
            applying_to_id=101
        )
        barbarians = Organization.objects.get(world_id=2, barbaric=True)

        response = self.client.get(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': barbarians.id
            })
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': barbarians.id
            })
        )
        self.assertEqual(response.status_code, 404)

    def test_diplomacy(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.DIPLOMACY,
            applying_to_id=101
        )

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'target_relationship': 'friendship'},
            follow=True
        )
        self.assertRedirects(
            response, Organization.objects.get(id=102).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.desired_relationship, 'friendship')

        self.client.get(
            reverse('character:activate', kwargs={'char_id': 7}),
            follow=True
        )

        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.DIPLOMACY,
            applying_to_id=105
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 101
            })
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 101
            }),
            data={'target_relationship': 'accept'},
            follow=True
        )

        self.assertRedirects(
            response, Organization.objects.get(id=106).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.relationship, 'friendship')
        self.assertEqual(relationship.desired_relationship, None)

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=105,
            to_organization_id=101,
        )
        self.assertEqual(relationship.relationship, 'friendship')
        self.assertEqual(relationship.desired_relationship, None)

    def test_diplomacy_reject(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.DIPLOMACY,
            applying_to_id=101
        )

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'target_relationship': 'friendship'},
            follow=True
        )
        self.assertRedirects(
            response, Organization.objects.get(id=102).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.desired_relationship, 'friendship')

        self.client.get(
            reverse('character:activate', kwargs={'char_id': 7}),
            follow=True
        )

        capability = Capability.objects.get(
            organization__id=106,
            type=Capability.DIPLOMACY,
            applying_to_id=105
        )

        response = self.client.get(capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 101
            })
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 101
            }),
            data={'target_relationship': 'refuse'},
            follow=True
        )

        self.assertRedirects(
            response, Organization.objects.get(id=106).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.relationship, 'peace')
        self.assertEqual(relationship.desired_relationship, None)

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=105,
            to_organization_id=101,
        )
        self.assertEqual(relationship.relationship, 'peace')
        self.assertEqual(relationship.desired_relationship, None)

    def test_diplomacy_take_back(self):
        capability = Capability.objects.get(
            organization__id=102,
            type=Capability.DIPLOMACY,
            applying_to_id=101
        )

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'target_relationship': 'friendship'},
            follow=True
        )
        self.assertRedirects(
            response, Organization.objects.get(id=102).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.desired_relationship, 'friendship')

        response = self.client.post(
            reverse('organization:diplomacy_capability', kwargs={
                'capability_id': capability.id,
                'target_organization_id': 105
            }),
            data={'target_relationship': 'take back'},
            follow=True
        )
        self.assertRedirects(
            response, Organization.objects.get(id=102).get_absolute_url()
        )

        relationship = OrganizationRelationship.objects.get(
            from_organization_id=101,
            to_organization_id=105,
        )
        self.assertEqual(relationship.desired_relationship, None)
