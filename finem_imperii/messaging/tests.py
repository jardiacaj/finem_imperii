from unittest.case import skip

from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from messaging.models import CharacterMessage, MessageRecipientGroup, MessageRecipient
from organization.models import Organization
from world.models import Character


class TestMessageModel(TestCase):
    fixtures = ['simple_world', 'simple_world_life']

    def test_get_nice_and_post_recipients(self):
        message = CharacterMessage.objects.create(creation_turn=0)
        kingdom_group = MessageRecipientGroup.objects.create(
            message=message,
            organization=Organization.objects.get(id=101)
        )
        MessageRecipient.objects.create(
            message=message,
            group=kingdom_group,
            character=Character.objects.get(id=1)
        )
        MessageRecipient.objects.create(
            message=message,
            group=kingdom_group,
            character=Character.objects.get(id=2)
        )
        MessageRecipient.objects.create(
            message=message,
            group=None,
            character=Character.objects.get(id=3)
        )

        recipient_list = message.get_nice_recipient_list()
        self.assertEqual(len(recipient_list), 2)
        self.assertIn(Organization.objects.get(id=101), recipient_list)
        self.assertIn(Character.objects.get(id=3), recipient_list)

        post_list = message.get_post_recipient_list()
        self.assertEqual(len(post_list), 2)
        self.assertIn("organization_101", post_list)
        self.assertIn("character_3", post_list)


class TestCompose(TestCase):
    fixtures = ['simple_world', 'simple_world_life']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        response = self.client.get(
            reverse('world:activate_character', kwargs={'char_id':1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('world:character_home'))

    def test_compose_view(self):
        response = self.client.get(reverse('messaging:compose'))
        self.assertEqual(response.status_code, 200)

    def test_compose_to_character_view(self):
        response = self.client.get(
            reverse('messaging:compose_character', kwargs={'character_id': 2}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, Character.objects.get(id=2).name)
