from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap analytics starter templates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--portfolio-id",
            action="append",
            type=int,
            dest="portfolio_ids",
            help="Bootstrap analytics starters for a specific portfolio id (repeatable).",
        )

    def handle(self, *args, **options):
        portfolio_ids = options.get("portfolio_ids") or []
        kwargs = {}
        if portfolio_ids:
            kwargs["portfolio_id"] = portfolio_ids
        call_command("seed_analytics_starters", **kwargs)
        self.stdout.write(self.style.SUCCESS("Analytics bootstrap complete."))
