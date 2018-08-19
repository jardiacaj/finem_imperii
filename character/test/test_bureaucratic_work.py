from django.test import TestCase
from django.urls.base import reverse

from character.models import Character
from turn.character import worldwide_character_travels
from world.initialization import initialize_settlement


class TestBureaucraticWork(TestCase):
    fixtures = ['simple_world']

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate', kwargs={'char_id': 8}),
            follow=True
        )
        self.character = Character.objects.get(id=8)

    def test_view(self):
        response = self.client.get(reverse('character:bureaucratic_work'))
        self.assertEqual(response.status_code, 200)

    def test_bureaucratic_work_does_not_fail(self):
        initialize_settlement(self.character.location)
        previous_po = self.character.location.public_order = 500
        self.character.location.save()
        response = self.client.post(
            reverse('character:bureaucratic_work'),
            data={
                'hours': 50
            },
            follow=True
        )

        self.assertRedirects(response, reverse('character:bureaucratic_work'))

        self.character.location.refresh_from_db()
        self.assertLess(previous_po, self.character.location.public_order)
