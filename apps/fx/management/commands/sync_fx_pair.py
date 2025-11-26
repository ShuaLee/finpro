from django.core.management.base import BaseCommand, CommandError
from fx.services.sync import FXSyncService


class Command(BaseCommand):
    help = "Sync a single FX pair (e.g., USD CAD)."

    def add_arguments(self, parser):
        parser.add_argument("base", type=str, help="Base currency (e.g. USD)")
        parser.add_argument("quote", type=str, help="Quote currency")

    def handle(self, *args, **options):
        base = options["base"].upper()
        quote = options["quote"].upper()

        self.stdout.write(f"Syncing FX pair: {base} -> {quote} ...")

        ok = FXSyncService.sync_single_pair(base, quote)

        if not ok:
            raise CommandError(
                f"Could not fetch FX rate for {base} -> {quote}.")

        self.stdout.write(
            self.style.SUCCESS(
                f"FX pair {base} -> {quote} synced successfully."
            )
        )
