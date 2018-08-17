from django.contrib import auth
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls.base import reverse


class TestAccountRegistration(TestCase):
    def setUp(self):
        # create one user for convenience
        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Alice',
                'email': 'alice@localhost',
                'password': 'supasecret',
                'password2': 'supasecret',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_registration(self):
        self.assertEqual(len(User.objects.all()), 1)
        user = User.objects.get(username='Alice')
        self.assertEqual(user.email, 'alice@localhost')

        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Bob',
                'email': 'bob@localhost',
                'password': 'foo',
                'password2': 'foo',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(User.objects.all()), 2)

    def test_duplicate_username(self):
        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Alice',
                'email': 'alice2@localhost',
                'password': 'supasecret',
                'password2': 'supasecret',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:register'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(User.objects.all()), 1)

    def test_duplicate_email(self):
        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Alice2000',
                'email': 'alice@localhost',
                'password': 'supasecret',
                'password2': 'supasecret',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:register'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(User.objects.all()), 1)

    def test_non_matching_passwords(self):
        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Bob',
                'email': 'bob@localhost',
                'password': 'foo',
                'password2': 'bar',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:register'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(User.objects.all()), 1)

    def test_form_view(self):
        response = self.client.get(reverse('account:register'))
        self.assertEqual(response.status_code, 200)


class TestLogin(TestCase):
    def setUp(self):
        # create one user for convenience
        response = self.client.post(
            reverse('account:register'),
            {
                'username': 'Alice',
                'email': 'alice@localhost',
                'password': 'supasecret',
                'password2': 'supasecret',
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:home'))
        self.assertEqual(response.status_code, 200)

    def test_disabled_login(self):
        user = User.objects.all().update(is_active=False)
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_wrong_credentials(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'wrong'},
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_wrong_user(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Bob', 'password': 'supasecret'},
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(reverse('account:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_being_logged_in(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        response = self.client.get(
            reverse('account:login'),
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:home'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.redirect_chain[0][0], reverse('account:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_while_not_logged_in(self):
        response = self.client.get(reverse('account:home'), follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].startswith(reverse('account:login')))
        self.assertEqual(response.status_code, 200)

    def test_home_view_while_logged_in(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        response = self.client.get(reverse('account:home'))
        self.assertEqual(response.status_code, 200)

    def test_register_view_while_logged_in(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        response = self.client.get(reverse('account:register'), follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].startswith(reverse('account:home')))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.post(
            reverse('account:login'),
            {'username': 'Alice', 'password': 'supasecret'},
            follow=True
        )
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)
        response = self.client.get(reverse('account:logout'), follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].startswith(reverse('base:home')))
        self.assertEqual(response.status_code, 200)
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
