from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="profileuser@example.com", password="password123")
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        url = reverse('profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('country', response.data)
        self.assertIn('preferred_currency', response.data)

    def test_update_profile(self):
        url = reverse('profile-detail')
        data = {"country": "GB", "preferred_currency": "GBP", "plan": "premium"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["country"], "GB")
        self.assertEqual(response.data["preferred_currency"], "GBP")
        self.assertEqual(response.data["plan"], "premium")

    def test_update_profile_account_type_and_plan(self):
        url = reverse('profile-detail')
        data = {"account_type": "manager", "plan": "premium"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["account_type"], "manager")
        self.assertEqual(response.data["plan"], "premium")