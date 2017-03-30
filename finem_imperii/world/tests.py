from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse


class TestHome(TestCase):
    fixtures = ['simple_world', 'simple_world_life']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)

    def test_activate_character(self):
        response = self.client.get(
            reverse('world:activate_character', kwargs={'char_id':1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('world:character_home'))
