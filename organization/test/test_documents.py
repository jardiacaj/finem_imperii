from django.test import TestCase
from django.urls.base import reverse

from organization.models import Capability, PolicyDocument


class TestDocuments(TestCase):
    fixtures = ["simple_world"]

    def setUp(self):
        self.client.post(
            reverse('account:login'),
            {'username': 'alice', 'password': 'test'},
        )
        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 1}),
            follow=True
        )
        self.capability = Capability.objects.get(
            organization__id=102,
            type=Capability.POLICY_DOCUMENT,
            applying_to_id=101
        )

    def test_view(self):
        response = self.client.get(self.capability.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_create_document_view(self):
        response = self.client.get(reverse(
            'organization:document_capability',
            kwargs={'capability_id': self.capability.id}
        ))
        self.assertEqual(response.status_code, 200)

    def test_create_public_document(self):
        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={'capability_id': self.capability.id}
            ),
            data={
                'title': 'Footitle',
                'body': 'Foocontent',
                'public': 'on'
            },
            follow=True
        )
        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())

        self.assertTrue(PolicyDocument.objects.exists())
        document = PolicyDocument.objects.get(id=1)
        self.assertEqual(document.body, 'Foocontent')
        self.assertEqual(document.title, 'Footitle')
        self.assertEqual(document.organization_id, 101)
        self.assertEqual(document.public, True)
        self.assertEqual(document.parent, None)
        self.assertEqual(document.last_modified_turn, 0)

        response = self.client.get(document.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foocontent')
        self.assertContains(response, 'Footitle')

        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 9}),
            follow=True
        )

        response = self.client.get(document.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foocontent')
        self.assertContains(response, 'Footitle')

    def test_create_private_document(self):
        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={'capability_id': self.capability.id}
            ),
            data={
                'title': 'Footitle',
                'body': 'Foocontent'
            },
            follow=True
        )
        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())

        self.assertTrue(PolicyDocument.objects.exists())
        document = PolicyDocument.objects.get(id=1)
        self.assertEqual(document.body, 'Foocontent')
        self.assertEqual(document.title, 'Footitle')
        self.assertEqual(document.organization_id, 101)
        self.assertEqual(document.public, False)
        self.assertEqual(document.parent, None)
        self.assertEqual(document.last_modified_turn, 0)

        response = self.client.get(document.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foocontent')
        self.assertContains(response, 'Footitle')

        self.client.get(
            reverse('character:activate_character', kwargs={'char_id': 9}),
            follow=True
        )

        response = self.client.get(document.get_absolute_url())
        self.assertRedirects(response, reverse('character:character_home'))

    def test_edit_document(self):
        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={'capability_id': self.capability.id}
            ),
            data={
                'title': 'Footitle',
                'body': 'Foocontent',
                'public': 'on'
            },
            follow=True
        )
        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())
        self.assertTrue(PolicyDocument.objects.exists())

        response = self.client.get(
            reverse(
                'organization:document_capability',
                kwargs={
                    'capability_id': self.capability.id,
                    'document_id': 1
                }
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foocontent')
        self.assertContains(response, 'Footitle')

        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={
                    'capability_id': self.capability.id,
                    'document_id': 1
                }
            ),
            data={
                'title': 'alttitle',
                'body': 'altcontent',
                'public': 'on'
            },
            follow=True
        )

        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())

        self.assertTrue(PolicyDocument.objects.exists())
        document = PolicyDocument.objects.get(id=1)
        self.assertEqual(document.body, 'altcontent')
        self.assertEqual(document.title, 'alttitle')
        self.assertEqual(document.organization_id, 101)
        self.assertEqual(document.public, True)
        self.assertEqual(document.parent, None)
        self.assertEqual(document.last_modified_turn, 0)

        response = self.client.get(document.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'altcontent')
        self.assertContains(response, 'alttitle')

    def test_delete_document(self):
        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={'capability_id': self.capability.id}
            ),
            data={
                'title': 'Footitle',
                'body': 'Foocontent',
                'public': 'on'
            },
            follow=True
        )
        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())
        self.assertTrue(PolicyDocument.objects.exists())

        response = self.client.post(
            reverse(
                'organization:document_capability',
                kwargs={
                    'capability_id': self.capability.id,
                    'document_id': 1
                }
            ),
            data={'delete': '1', },
            follow=True
        )

        self.assertRedirects(response,
                             self.capability.organization.get_absolute_url())
        self.assertFalse(PolicyDocument.objects.exists())
