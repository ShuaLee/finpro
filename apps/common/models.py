from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta

class FXRate(models.Model):
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('from_currency', 'to_currency')]

    def __str__(self):
        return f"{self.from_currency} → {self.to_currency}: {self.rate}"

    def is_stale(self):
        return self.updated_at < timezone.now() - timedelta(hours=24)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        def _after_commit():
            from schemas.services.recalc_triggers import recalc_holdings_for_fx_pair
            recalc_holdings_for_fx_pair(self.from_currency, self.to_currency)

        transaction.on_commit(_after_commit)
