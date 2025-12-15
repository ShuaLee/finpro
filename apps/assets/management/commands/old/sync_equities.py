# assets/management/commands/sync_equities.py

from django.core.management.base import BaseCommand
from assets.services.syncs.equity_sync import EquitySyncService


class Command(BaseCommand):
    help = (
        "Sync or seed the full equity universe from FMP. "
        "Handles new IPOs, renamed tickers, and delistings. "
        "Can run safely multiple times."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without saving changes (for testing).",
        )
        parser.add_argument(
            "--exchange",
            type=str,
            default=None,
            help="Optional exchange filter (e.g. NYSE, NASDAQ).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        exchange = options["exchange"]

        # --- Banner ---
        mode = "[DRY RUN]" if dry_run else "[LIVE SYNC]"
        scope = exchange or "ALL EXCHANGES"
        self.stdout.write(self.style.NOTICE(
            f"Starting equity sync {mode} for {scope}"))

        # --- Execute ---
        results = EquitySyncService.sync_universe(
            exchange=exchange,
            dry_run=dry_run,
        )

        # --- Print Results ---
        created = results.get("created", 0)
        collisions = results.get("collisions", 0)
        delisted = results.get("delisted", 0)
        hydrated_profiles = results.get("hydrated_profiles", 0)
        hydrated_quotes = results.get("hydrated_quotes", 0)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "✅ Equity universe sync completed"))
        self.stdout.write(f" • Created:          {created}")
        self.stdout.write(f" • Collisions:       {collisions}")
        self.stdout.write(f" • Delisted:         {delisted}")
        self.stdout.write(f" • Hydrated profiles:{hydrated_profiles}")
        self.stdout.write(f" • Hydrated quotes:  {hydrated_quotes}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Dry run complete — no DB changes made."))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Database updated successfully."))

        self.stdout.write("")  # newline
