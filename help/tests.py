from django.test import TestCase
from django.urls.base import reverse


class HelpPageTestCase(TestCase):
    def test_homepage(self):
        response = self.client.get(reverse('help:home'))
        self.assertEqual(response.status_code, 200)
