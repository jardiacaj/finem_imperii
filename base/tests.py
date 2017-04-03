from django.test import TestCase

from django.urls.base import reverse


class HomepageTestCase(TestCase):
    fixtures = ['simple_world']

    def test_homepage_unauthenticated(self):
        response = self.client.get(reverse('base:home'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_authenticated(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        response = self.client.get(reverse('base:home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:home'))


class HelpPageTestCase(TestCase):
    def test_homepage(self):
        response = self.client.get(reverse('base:help'))
        self.assertEqual(response.status_code, 200)
