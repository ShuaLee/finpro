from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()

class UserManagerTests(TestCase):
    def test_profile_created_for_new_user(self):
        """
        When a user is created via manager, a Profile should be auto-created.
        """
        user = User.objects.create_user(email="testmanager@example.com", password="securePass123")
        self.assertTrue(Profile.objects.filter(user=user).exists(), "Profile was not created for user")

    def test_profile_created_for_superuser(self):
        """
        When a superuser is created, a Profile should also be auto-created.
        """
        superuser = User.objects.create_superuser(email="admin@example.com", password="securePass123")
        self.assertTrue(Profile.objects.filter(user=superuser).exists(), "Profile was not created for superuser")