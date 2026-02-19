from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portfolios.models import Portfolio
from portfolios.services import PortfolioValuationService


class Command(BaseCommand):
    help = "Bootstrap portfolio-level defaults (denominations)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--portfolio-id",
            action="append",
            type=int,
            dest="portfolio_ids",
            help="Bootstrap a specific portfolio id (repeatable).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        portfolio_ids = options.get("portfolio_ids") or []
        if portfolio_ids:
            ids = set(Portfolio.objects.filter(id__in=portfolio_ids).values_list("id", flat=True))
            missing = [pid for pid in portfolio_ids if pid not in ids]
            if missing:
                raise CommandError(f"Unknown portfolio id(s): {missing}")
            queryset = Portfolio.objects.filter(id__in=ids).select_related("profile__currency").order_by("id")
        else:
            queryset = Portfolio.objects.select_related("profile__currency").order_by("id")

        count = 0
        for portfolio in queryset:
            PortfolioValuationService.ensure_default_denominations(portfolio=portfolio)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Portfolios bootstrap complete for {count} portfolio(s)."))
