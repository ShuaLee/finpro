from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.services.bootstrap_service import ProfileBootstrapService
from users.models import User


@receiver(post_save, sender=User)
def bootstrap_profile_for_new_user(sender, instance, created, **kwargs):
    if not created:
        return

    # Run after commit so all user data is persisted before bootstrap creates dependents.
    transaction.on_commit(lambda: ProfileBootstrapService.bootstrap(user=instance))

