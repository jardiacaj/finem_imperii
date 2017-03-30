from django.test import TestCase

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
