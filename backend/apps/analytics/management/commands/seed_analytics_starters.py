from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analytics.seeders import seed_starter_templates_for_portfolio
from portfolios.models import Portfolio


class Command(BaseCommand):
    help = "Seed analytics starter templates for portfolios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--portfolio-id",
            action="append",
            type=int,
            dest="portfolio_ids",
            help="Seed a specific portfolio id (can be repeated).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        portfolio_ids = options.get("portfolio_ids") or []

        if portfolio_ids:
            found_ids = set(Portfolio.objects.filter(id__in=portfolio_ids).values_list("id", flat=True))
            missing = [pid for pid in portfolio_ids if pid not in found_ids]
            if missing:
                raise CommandError(f"Unknown portfolio id(s): {missing}")
            ids_to_seed = sorted(found_ids)
        else:
            ids_to_seed = list(Portfolio.objects.order_by("id").values_list("id", flat=True))

        total_a = 0
        total_d = 0
        total_b = 0

        for portfolio_id in ids_to_seed:
            stats = seed_starter_templates_for_portfolio(portfolio_id=portfolio_id)
            total_a += stats["analytics_created"]
            total_d += stats["dimensions_created"]
            total_b += stats["buckets_created"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded analytics starters for {len(ids_to_seed)} portfolio(s): "
                f"analytics={total_a}, dimensions={total_d}, buckets={total_b}."
            )
        )
