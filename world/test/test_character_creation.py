from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from organization.models import Organization
from world.models import Character


class TestCharacterCreation(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)

    def test_create_character_in_kingdom(self):
        response = self.client.post(
            reverse('world:create_character', kwargs={'world_id': 2}),
            data={
                'state_id': Organization.objects.get(name="Small Kingdom").id,
                'name': 'Rusbel',
                'surname': 'Gossett'
            },
            follow=True
        )

        new_character = Character.objects.get(name="Rusbel Gossett")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('world:activate_character', kwargs={'char_id': new_character.id})
        )
        self.assertEqual(response.redirect_chain[1][1], 302)
        self.assertEqual(response.redirect_chain[1][0], reverse('world:character_home'))