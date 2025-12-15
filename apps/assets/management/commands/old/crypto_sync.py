from django.core.management.base import BaseCommand
from assets.services.syncs.crypto_sync import CryptoSyncService


class Command(BaseCommand):
    help = (
        "Sync or seed the full cryptocurrency universe from FMP. "
        "Adds newly-listed tokens and updates names/metadata. "
        "Safe to run nightly or on-demand."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without writing any DB changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        mode = "[DRY RUN]" if dry_run else "[LIVE SYNC]"
        self.stdout.write(self.style.NOTICE(
            f"Starting cryptocurrency universe sync {mode}"
        ))

        # --- Execute ---
        results = CryptoSyncService.sync_universe(dry_run=dry_run)

        created = results.get("created", 0)
        updated = results.get("updated", 0)

        # --- Output ---
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "✅ Crypto universe sync completed"))
        self.stdout.write(f" • Created new tokens:   {created}")
        self.stdout.write(f" • Updated existing:     {updated}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Dry run complete — no DB updates applied."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Database updated successfully."
            ))

        self.stdout.write("")  # newline
