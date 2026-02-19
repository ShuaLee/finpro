from django.core.management.base import BaseCommand

from core.services import FinproBootstrapOrchestrator


class Command(BaseCommand):
    help = "Bootstrap FinPro in dependency order (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-migrate",
            action="store_true",
            help="Run `migrate` as the first bootstrap step.",
        )
        parser.add_argument(
            "--skip-market-data",
            action="store_true",
            help="Skip network-heavy asset universe refresh during assets bootstrap.",
        )
        parser.add_argument(
            "--portfolio-id",
            action="append",
            type=int,
            dest="portfolio_ids",
            help="Limit portfolio/analytics bootstrap to specific portfolio id(s).",
        )

    def handle(self, *args, **options):
        FinproBootstrapOrchestrator.run(
            stdout=self.stdout,
            style=self.style,
            include_migrate=options["with_migrate"],
            skip_market_data=options["skip_market_data"],
            portfolio_ids=options.get("portfolio_ids") or [],
        )
