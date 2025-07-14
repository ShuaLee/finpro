from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from finances.models import FXRate

class FXRateTests(TestCase):
    def test_fxrate_staleness(self):
        recent = FXRate.objects.create(from_currency="USD", to_currency="EUR", rate=1.1)
        self.assertFalse(recent.is_stale())

        stale_time = timezone.now() - timedelta(days=2)
        FXRate.objects.filter(pk=recent.pk).update(updated_at=stale_time)
        recent.refresh_from_db()
        self.assertTrue(recent.is_stale())