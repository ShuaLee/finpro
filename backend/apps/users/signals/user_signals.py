from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import User
from apps.users.services import ProfileCreationService


@receiver(post_save, sender=User)
def ensure_profile_for_user(sender, instance, created, **kwargs):
    if created:
        ProfileCreationService.ensure_profile(user=instance)
