from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from organization.models import Organization
from character.models import Character


class TestCharacterCreation(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        user.is_superuser = True
        user.save()
        self.assertEqual(User.objects.get(id=1), user)

    def test_step1_view(self):
        response = self.client.post(
            reverse('character:create_character'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_step2_view(self):
        response = self.client.post(
            reverse('character:create_character', kwargs={'world_id': 2}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_create_commander_in_kingdom(self):
        response = self.client.post(
            reverse('character:create_character', kwargs={'world_id': 2}),
            data={
                'state_id': Organization.objects.get(name="Small Kingdom").id,
                'name': 'Rusbel',
                'surname': 'Gossett',
                'profile': 'commander'
            },
            follow=True
        )

        new_character = Character.objects.get(name="Rusbel Gossett")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('character:activate_character', kwargs={'char_id': new_character.id})
        )
        self.assertEqual(response.redirect_chain[1][1], 302)
        self.assertEqual(response.redirect_chain[1][0], reverse('character:character_home'))

    def test_create_trader_in_commonwealth(self):
        response = self.client.post(
            reverse('character:create_character', kwargs={'world_id': 2}),
            data={
                'state_id': Organization.objects.get(name="Small Commonwealth").id,
                'name': 'Rusbel',
                'surname': 'Gossett',
                'profile': 'trader'
            },
            follow=True
        )

        new_character = Character.objects.get(name="Rusbel Gossett")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('character:activate_character', kwargs={'char_id': new_character.id})
        )
        self.assertEqual(response.redirect_chain[1][1], 302)
        self.assertEqual(response.redirect_chain[1][0], reverse('character:character_home'))

    def test_create_barbaric_bureaucrat(self):
        response = self.client.post(
            reverse('character:create_character', kwargs={'world_id': 2}),
            data={
                'state_id': Organization.objects.get(name="Barbarians of Parvus").id,
                'name': 'Rusbel',
                'surname': 'Gossett',
                'profile': 'bureaucrat'
            },
            follow=True
        )

        new_character = Character.objects.get(name="Rusbel Gossett")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('character:activate_character', kwargs={'char_id': new_character.id})
        )
        self.assertEqual(response.redirect_chain[1][1], 302)
        self.assertEqual(response.redirect_chain[1][0], reverse('character:character_home'))
