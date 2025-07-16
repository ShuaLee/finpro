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


from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Profile
from subscriptions.models import Plan, AccountType
from users.services import bootstrap_user_profile_and_portfolio


class ProfileTests(APITestCase):
    """
    Tests Profile-related API operations with JWT cookie-based authentication.

    Setup:
    - Creates a user.
    - Creates subscription plans: Free and Premium.
    - Creates AccountType (required for bootstrap).
    - Bootstraps Profile and Portfolio for the user.
    - Logs the user in and attaches JWT cookies for authenticated requests.
    """

    def setUp(self):
        # 1. Create user
        self.user_email = "user@example.com"
        self.password = "testpass"
        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.password,
            is_over_13=True
        )

        # 2. Create subscription plans
        self.free_plan = Plan.objects.create(
            name="Free", slug="free", description="Free plan", price_per_month=0, is_active=True
        )
        self.premium_plan = Plan.objects.create(
            name="Premium", slug="premium", description="Premium plan", price_per_month=9.99, is_active=True
        )

        # 3. Create AccountType (needed for bootstrap)
        self.account_type = AccountType.objects.create(
            name="Individual Investor",
            slug="individual",
            description="Default account type"
        )

        # 4. Bootstrap Profile and Portfolio
        bootstrap_user_profile_and_portfolio(self.user)
        self.profile = Profile.objects.get(user=self.user)
        self.profile.plan = self.free_plan
        self.profile.save()

        # 5. Authenticate using JWT cookies
        login_url = reverse("cookie-login")  # ✅ Correct URL name
        response = self.client.post(
            login_url,
            {"email": self.user_email, "password": self.password},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Login failed")

        # Attach JWT tokens as cookies for subsequent requests
        self.client.cookies["access"] = response.cookies.get("access").value
        self.client.cookies["refresh"] = response.cookies.get("refresh").value

        # Profile plan update endpoint
        self.url = reverse("update-profile-plan")

    def test_update_plan_success(self):
        """
        Ensure:
        - Sending PATCH request with "premium" slug updates profile plan.
        - Response returns HTTP 200.
        """
        response = self.client.patch(self.url, {"plan": "premium"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.plan.slug, "premium")

    def test_update_plan_invalid_slug(self):
        """
        Ensure:
        - Sending PATCH request with an invalid slug returns 400.
        - Response includes an error for "plan".
        """
        response = self.client.patch(self.url, {"plan": "invalid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data)