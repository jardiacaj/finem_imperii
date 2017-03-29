from django.test import TestCase

from django.urls.base import reverse


class HomepageTestCase(TestCase):
    def test_homepage(self):
        response = self.client.get(reverse('base:home'))
        self.assertEqual(response.status_code, 200)
