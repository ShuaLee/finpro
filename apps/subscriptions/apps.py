from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        from subscriptions.models import Plan
        try:
            Plan.objects.get_or_create(
                slug='free',
                defaults={
                    'name': 'Free',
                    'description': 'Basic plan with limited features',
                    'max_stocks': 10,
                    'allow_crypto': False,
                    'allow_metals': False,
                    'price_per_month': 0.00
                }
            )
            Plan.objects.get_or_create(
                slug='premium',
                defaults={
                    'name': 'Premium',
                    'description': 'Unlimited access with crypto and metals',
                    'max_stocks': 9999,
                    'allow_crypto': True,
                    'allow_metals': True,
                    'price_per_month': 9.99
                }
            )
        except Exception:
            pass  # avoid errord during migrate
