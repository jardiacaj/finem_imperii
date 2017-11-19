from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse

from messaging.models import CharacterMessage, MessageRecipientGroup, MessageRecipient, MessageRelationship
from organization.models import Organization
from character.models import Character


class TestMessageModel(TestCase):
    fixtures = ['simple_world']

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
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        user = auth.get_user(self.client)
        self.assertEqual(User.objects.get(id=1), user)
        response = self.client.get(
            reverse('character:activate', kwargs={'char_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))

    def test_compose_view(self):
        response = self.client.get(reverse('messaging:compose'))
        self.assertEqual(response.status_code, 200)

    def test_compose_to_character_view(self):
        response = self.client.get(
            reverse('messaging:compose_character', kwargs={'character_id': 2}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, Character.objects.get(id=2).name)

    def test_send_empty_message(self):
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': '',
                'recipient': ['character_2', ]
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CharacterMessage.objects.all().count(), 0)

    def test_send_too_long_message(self):
        message_body = 'A' * 20000
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_2', ]
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 0)

    def test_send_no_recipients(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 0)

    def test_send_message_to_character_and_organizations(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['organization_101', 'organization_102', 'character_3']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 2)
        self.assertTrue(MessageRecipientGroup.objects.filter(organization_id=101).exists())
        self.assertTrue(MessageRecipientGroup.objects.filter(organization_id=102).exists())
        self.assertEqual(MessageRecipient.objects.all().count(), 3)
        self.assertTrue(MessageRecipient.objects.filter(character_id=3, group=None).exists())

    def test_send_message_to_settlement(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['settlement']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 2)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None).exists())
        self.assertTrue(MessageRecipient.objects.filter(character_id=2, group=None).exists())

    def test_send_message_to_tile(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['region']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 3)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None).exists())
        self.assertTrue(MessageRecipient.objects.filter(character_id=2, group=None).exists())
        self.assertTrue(MessageRecipient.objects.filter(character_id=3, group=None).exists())

    def test_send_message_to_invalid_recipient(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['foobar']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 0)

    def test_send_and_reply_character(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_1']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None).exists())

        response = self.client.get(reverse('messaging:reply', kwargs={'recipient_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, message_body)
        self.assertContains(response, 'reply_to')

        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'reply_to': '1'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 2)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 2)

    def test_send_and_reply_organization(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['organization_101']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 1)
        self.assertEqual(MessageRecipient.objects.all().count(), 2)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1).exists())
        self.assertTrue(MessageRecipient.objects.filter(character_id=2).exists())

        response = self.client.get(reverse('messaging:reply', kwargs={'recipient_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, message_body)
        self.assertContains(response, 'reply_to')

        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'reply_to': '1'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 2)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 1 + 1)
        self.assertEqual(MessageRecipient.objects.all().count(), 2 + 2)

    def test_send_and_reply_non_own_message(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_2']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=2, group=None).exists())

        response = self.client.get(reverse('messaging:reply', kwargs={'recipient_id': 1}))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'reply_to': '1'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)

    def test_send_and_mark_read_non_own_message(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_2']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=2, group=None).exists())

        response = self.client.get(reverse('messaging:mark_read', kwargs={'recipient_id': 1}))
        self.assertEqual(response.status_code, 404)

    def test_send_and_mark_favourite_non_own_message(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_2']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=2, group=None).exists())

        response = self.client.get(reverse('messaging:mark_favourite', kwargs={'recipient_id': 1}))
        self.assertEqual(response.status_code, 404)


    def test_mark_all_as_read(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_1']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, read=False).exists())

        response = self.client.get(
            reverse('messaging:mark_all_read'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, read=True).exists())
        self.assertFalse(MessageRecipient.objects.filter(character_id=1, group=None, read=False).exists())

    def test_mark_as_read(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_1']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, read=False).exists())

        response = self.client.get(
            reverse('messaging:mark_read', kwargs={'recipient_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:home'))
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, read=True).exists())
        self.assertFalse(MessageRecipient.objects.filter(character_id=1, group=None, read=False).exists())
        self.assertNotContains(response, message_body)

        response = self.client.get(reverse('messaging:messages_list'))
        self.assertContains(response, message_body)

        response = self.client.get(reverse('messaging:sent'))
        self.assertContains(response, message_body)

        response = self.client.get(
            reverse('messaging:mark_read', kwargs={'recipient_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:home'))
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, read=False).exists())
        self.assertFalse(MessageRecipient.objects.filter(character_id=1, group=None, read=True).exists())
        self.assertContains(response, message_body)

    def test_message_favourite_unfavourite(self):
        message_body = 'Nice to meet you, foobar.'
        response = self.client.post(
            reverse('messaging:compose'),
            data={
                'message_body': message_body,
                'recipient': ['character_1']
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:sent'))
        self.assertContains(response, message_body)
        self.assertEqual(CharacterMessage.objects.all().count(), 1)
        self.assertEqual(MessageRecipientGroup.objects.all().count(), 0)
        self.assertEqual(MessageRecipient.objects.all().count(), 1)
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, favourite=False).exists())

        response = self.client.get(reverse('messaging:favourites'))
        self.assertNotContains(response, message_body)

        response = self.client.get(
            reverse('messaging:mark_favourite', kwargs={'recipient_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:home'))
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, favourite=True).exists())
        self.assertFalse(MessageRecipient.objects.filter(character_id=1, group=None, favourite=False).exists())

        response = self.client.get(reverse('messaging:favourites'))
        self.assertContains(response, message_body)

        response = self.client.get(
            reverse('messaging:mark_favourite', kwargs={'recipient_id': 1}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('messaging:home'))
        self.assertTrue(MessageRecipient.objects.filter(character_id=1, group=None, favourite=False).exists())
        self.assertFalse(MessageRecipient.objects.filter(character_id=1, group=None, favourite=True).exists())
        self.assertContains(response, message_body)

        response = self.client.get(reverse('messaging:favourites'))
        self.assertNotContains(response, message_body)

    def test_add_and_remove_contact(self):
        target_character = Character.objects.get(id=3)

        response = self.client.get(reverse('messaging:compose'))
        self.assertContains(response, target_character.name, count=1)

        response = self.client.get(
            reverse('messaging:add_contact', kwargs={'character_id': target_character.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))
        self.assertTrue(MessageRelationship.objects.filter(from_character_id=1, to_character=target_character).exists())

        response = self.client.get(reverse('messaging:compose'))
        self.assertContains(response, target_character.name, count=2)

        response = self.client.get(
            reverse('messaging:add_contact', kwargs={'character_id': target_character.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))
        self.assertTrue(MessageRelationship.objects.filter(from_character_id=1, to_character=target_character).exists())

        response = self.client.get(reverse('messaging:compose'))
        self.assertContains(response, target_character.name, count=2)

        response = self.client.get(
            reverse('messaging:remove_contact', kwargs={'character_id': target_character.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))
        self.assertFalse(MessageRelationship.objects.filter(from_character_id=1, to_character=target_character).exists())

        response = self.client.get(reverse('messaging:compose'))
        self.assertContains(response, target_character.name, count=1)

        response = self.client.get(
            reverse('messaging:remove_contact', kwargs={'character_id': target_character.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('character:character_home'))
        self.assertFalse(MessageRelationship.objects.filter(from_character_id=1, to_character=target_character).exists())

        response = self.client.get(reverse('messaging:compose'))
        self.assertContains(response, target_character.name, count=1)
