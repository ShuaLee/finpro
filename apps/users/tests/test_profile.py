"""
users.tests.test_profile
~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for Profile API endpoints, including subscription plan updates.

Key scenarios tested:
- A user can successfully upgrade from the Free plan to Premium using JWT cookie authentication.
- Providing an invalid plan slug returns an appropriate error response.
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Profile
from subscriptions.models import Plan
from users.services import bootstrap_user_profile_and_portfolio


class ProfileTests(APITestCase):
    """
    Tests Profile-related API operations with JWT authentication.

    Setup:
        - Creates a user and logs in via JWT cookie-based auth.
        - Ensures the user's Profile exists using bootstrap service.
        - Creates two subscription plans: Free and Premium.
        - Assigns the Free plan to the user's profile.
    """

    def setUp(self):
        # Step 1: Create user
        self.user_email = "user@example.com"
        self.password = "testpass"
        self.user = User.objects.create_user(
            email=self.user_email,
            first_name="John",
            password=self.password,
            is_over_13=True,
        )

        # Step 2: Create subscription plans
        self.free_plan = Plan.objects.create(
            name="Free", slug="free", description="Free plan", price_per_month=0
        )
        self.premium_plan = Plan.objects.create(
            name="Premium", slug="premium", description="Premium plan", price_per_month=9.99
        )

        # Step 3: Bootstrap Profile and Portfolio
        bootstrap_user_profile_and_portfolio(self.user)
        self.profile = Profile.objects.get(user=self.user)
        self.profile.plan = self.free_plan
        self.profile.save()

        # Step 4: Authenticate using JWT cookies
        login_url = reverse("login")  # Make sure this matches your URL name
        response = self.client.post(
            login_url,
            {"email": self.user_email, "password": self.password},
            format="json"
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, "Login failed")

        # Attach JWT tokens as cookies
        self.client.cookies["access"] = response.cookies.get("access").value
        self.client.cookies["refresh"] = response.cookies.get("refresh").value

        # Profile update endpoint
        self.url = reverse("update-profile-plan")

    def test_update_plan_success(self):
        """
        Test successful plan update:
        - Sends PATCH request with "premium" slug.
        - Expects HTTP 200 OK.
        - Confirms profile.plan is updated to Premium.
        """
        response = self.client.patch(
            self.url, {"plan": "premium"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.plan.slug, "premium")

    def test_update_plan_invalid_slug(self):
        """
        Test invalid plan update:
        - Sends PATCH request with a non-existent plan slug.
        - Expects HTTP 400 Bad Request.
        - Response should include an error for "plan".
        """
        response = self.client.patch(
            self.url, {"plan": "invalid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data)
