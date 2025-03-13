from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IndividualPortfolio
from core.models import Profile


@receiver(post_save, sender=Profile)
def create_individual_portfolio(sender, instance, created, **kwargs):
    # Create an IndividualPortfolio when a profile is first created
    if created:
        IndividualPortfolio.objects.create(
            profile=instance
        )
