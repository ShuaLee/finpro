from apps.users.models import Profile, User


class ProfileCreationService:
    @staticmethod
    def ensure_profile(
        *,
        user: User,
        full_name: str = "",
        language: str = "en",
        timezone: str = "UTC",
        currency: str = "USD",
    ) -> Profile:
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                "full_name": full_name,
                "language": language,
                "timezone": timezone,
                "currency": currency,
            },
        )

        if not created:
            updated = False

            if full_name and profile.full_name != full_name:
                profile.full_name = full_name
                updated = True

            if profile.language != language:
                profile.language = language
                updated = True

            if profile.timezone != timezone:
                profile.timezone = timezone
                updated = True

            if profile.currency != currency:
                profile.currency = currency
                updated = True

            if updated:
                profile.save()

        return profile

    @staticmethod
    def update_profile(
        *,
        user: User,
        full_name: str = "",
        language: str = "en",
        timezone: str = "UTC",
        currency: str = "USD",
    ) -> Profile:
        profile = ProfileCreationService.ensure_profile(user=user)

        profile.full_name = full_name
        profile.language = language
        profile.timezone = timezone
        profile.currency = currency
        profile.save()

        return profile
