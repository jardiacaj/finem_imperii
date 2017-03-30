from django.test import TestCase

from organization.models import Organization
from world.models import Character


class TestOrganizationModel(TestCase):
    fixtures = ["simple_world"]

    def test_get_descendants_excluding_self(self):
        kingdom = Organization.objects.get(name="Small Kingdom")
        descendants = kingdom.get_descendants_list()
        self.assertEqual(len(descendants), 3)
        self.assertIn(Organization.objects.get(name="Governor of some forest"), descendants)
        self.assertIn(Organization.objects.get(name="Governor of some plains"), descendants)
        self.assertIn(Organization.objects.get(name="Helper of the governor of some plains"), descendants)

    def test_get_descendants_including_self(self):
        kingdom = Organization.objects.get(name="Governor of some plains")
        descendants = kingdom.get_descendants_list(including_self=True)
        print(descendants)
        self.assertEqual(len(descendants), 2)
        self.assertIn(Organization.objects.get(name="Governor of some plains"), descendants)
        self.assertIn(Organization.objects.get(name="Helper of the governor of some plains"), descendants)

    def test_get_membership_including_descendants(self):
        kingdom = Organization.objects.get(name="Governor of some plains")
        membership = kingdom.get_membership_including_descendants()
        self.assertEqual(len(membership), 1)
        self.assertIn(Character.objects.get(id=2), membership)

    def test_get_membership_including_descendants2(self):
        kingdom = Organization.objects.get(name="Small Kingdom")
        membership = kingdom.get_membership_including_descendants()
        self.assertEqual(len(membership), 2)
        self.assertIn(Character.objects.get(id=1), membership)
        self.assertIn(Character.objects.get(id=2), membership)
