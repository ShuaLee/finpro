from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

# Signal to automatically create a Prolfile when a User is created


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
