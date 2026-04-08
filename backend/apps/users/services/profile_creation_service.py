from apps.users.models import Profile, User
from apps.users.services.reference_data_service import ReferenceDataService


class ProfileCreationService:
    @staticmethod
    def ensure_profile(
        *,
        user: User,
        full_name: str = "",
        language: str = "en",
        timezone: str = "UTC",
        country: str = "",
        currency: str = "USD",
    ) -> Profile:
        normalized_country = ReferenceDataService.validate_country_code(country)
        normalized_currency = ReferenceDataService.validate_currency_code(currency)
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                "full_name": full_name,
                "language": language,
                "timezone": timezone,
                "country": normalized_country,
                "currency": normalized_currency,
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

            if profile.country != normalized_country:
                profile.country = normalized_country
                updated = True

            if profile.currency != normalized_currency:
                profile.currency = normalized_currency
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
        country: str = "",
        currency: str = "USD",
    ) -> Profile:
        profile = getattr(user, "profile", None)
        if profile is None:
            profile = ProfileCreationService.ensure_profile(
                user=user,
                full_name=full_name,
                language=language,
                timezone=timezone,
                country=country,
                currency=currency,
            )
        normalized_country = ReferenceDataService.validate_country_code(country)
        normalized_currency = ReferenceDataService.validate_currency_code(currency)

        updated = False

        if profile.full_name != full_name:
            profile.full_name = full_name
            updated = True

        if profile.language != language:
            profile.language = language
            updated = True

        if profile.timezone != timezone:
            profile.timezone = timezone
            updated = True

        if profile.country != normalized_country:
            profile.country = normalized_country
            updated = True

        if profile.currency != normalized_currency:
            profile.currency = normalized_currency
            updated = True

        if updated:
            profile.save()

        return profile
