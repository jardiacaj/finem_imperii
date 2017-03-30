from django.test import TestCase

from organization.models import Organization


class TestOrganizationModel(TestCase):
    fixtures = ["simple_world", "simple_world_life"]

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
