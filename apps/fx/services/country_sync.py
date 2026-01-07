import logging
import pycountry

from fx.models.country import Country
from external_data.providers.fmp.fx.fetchers import fetch_available_countries

logger = logging.getLogger(__name__)


class CountrySyncService:

    @classmethod
    def sync_countries(cls) -> int:
        """
        Sync country codes from FMP and enrich them with pycountry names.
        Returns the number of countries created or updated.
        """
        codes = fetch_available_countries()

        if not codes:
            logger.warning("No countries returned from FMP.")
            return 0

        created = 0
        updated = 0

        for code in codes:
            code = code.upper().strip()
            name = cls._lookup_country_name(code)

            obj, was_created = Country.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )

            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(
            f"Country sync complete - {created} created, {updated} updated")
        return created + updated

    # ------------------------------------------------------------
    # Lookup helper
    # ------------------------------------------------------------
    @staticmethod
    def _lookup_country_name(code: str) -> str:
        """
        Returns full ISO country name using pycountry.
        Fallback: return the code itself as the name.
        """
        if not code:
            return "Unknown"

        try:
            c = pycountry.countries.get(alpha_2=code)
            return c.name if c else code
        except Exception:
            return code
