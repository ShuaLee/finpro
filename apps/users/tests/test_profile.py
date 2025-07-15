from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profileuser@example.com",
            password="password123",
            first_name="John",
            is_over_13=True
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('profile-detail')  # Ensure matches your router name

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('country', response.data)
        self.assertIn('preferred_currency', response.data)

    def test_partial_update_profile(self):
        data = {"country": "GB", "preferred_currency": "GBP", "plan": "premium"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["country"], "GB")
        self.assertEqual(response.data["preferred_currency"], "GBP")
        self.assertEqual(response.data["plan"], "premium")

    def test_update_account_type_and_plan(self):
        data = {"account_type": "manager", "plan": "premium"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["account_type"], "manager")
        self.assertEqual(response.data["plan"], "premium")

    def test_put_requires_country_and_currency(self):
        # Full update should fail if required fields missing
        response = self.client.put(self.url, {"language": "es"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.json()["detail"])
