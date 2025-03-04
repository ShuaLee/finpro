from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Portfolio
from core.models import Profile


@receiver(post_save, sender=Profile)
def create_portfolio(sender, instance, created, **kwargs):
    # Only create a portfolio when a profile is first created
    if created:
        if instance.role == 'individual':
            Portfolio.objects.create(
                individual_profile=instance, name=f"{instance.user.email}'s Portfolio")
        elif instance.role == 'asset_manager':
            # Asset managers will create portfolios as needed, so we don't automatically create one here
            pass
