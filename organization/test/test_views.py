from django.test import TestCase
from django.urls.base import reverse

from organization.models import Organization


class TestViews(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        response = self.client.get(
            reverse('character:activate', kwargs={'char_id': 1}),
            follow=True
        )

    def test_view(self):
        for org in Organization.objects.all():
            response = self.client.get(org.get_absolute_url())
            self.assertEqual(response.status_code, 200)
