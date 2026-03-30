from typing import cast

from django.db import transaction

from apps.users.models import Profile, User
from apps.users.models.user import UserManager


class UserCreationService:
    @staticmethod
    @transaction.atomic
    def create_user(
        *,
        email: str,
        password: str,
        full_name: str = "",
        language: str = "en",
        timezone: str = "UTC",
        currency: str = "USD",
        country_code: str = "",
        is_active: bool = True,
    ) -> User:
        user_manager = cast(UserManager, User.objects)

        user = user_manager.create_user(
            email=email,
            password=password,
            is_active=is_active,
        )

        Profile.objects.create(
            user=user,
            full_name=full_name,
            language=language,
            timezone=timezone,
            currency=currency,
            country_code=country_code,
        )

        return user
