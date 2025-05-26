from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management.base import CommandError
from datetime import datetime

class Command(BaseCommand):
    help = 'Create a superuser with birth_date required for linked Profile'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--birth_date',
            dest='birth_date',
            default=None,
            help='Birth date in YYYY-MM-DD format',
        )

    def handle(self, *args, **options):
        birth_date = options.get('birth_date')

        # If not provided and in interactive mode, prompt manually
        if not birth_date and not options.get('noinput'):
            while True:
                try:
                    birth_date = input('Birth Date (YYYY-MM-DD): ').strip()
                    if not birth_date:
                        self.stderr.write("Error: Birth date cannot be empty.")
                        continue
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                    break
                except ValueError:
                    self.stderr.write("Error: Invalid date format. Use YYYY-MM-DD.")
        elif birth_date:
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError("Invalid birth_date format. Use YYYY-MM-DD.")

        elif not birth_date and options.get('noinput'):
            raise CommandError("You must provide --birth_date when using --noinput.")

        # Inject parsed date into options
        options['birth_date'] = birth_date
        super().handle(*args, **options)