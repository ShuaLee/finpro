from django.db import models
from core.models import Profile
# Create your models here.


class Portfolio(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile} - {self.created_at}"

class Asset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    investment_theme = models.ManyToManyField('InvestmentTheme', related_name="assets", blank=True)

    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__
    
    def get_current_value(self):
        raise NotImplementedError
    

class InvestmentTheme(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='asset_tags')
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtags')

    class Meta:
        unique_together = ('portfolio', 'name')

    def __str__(self):
        full_path = [self.name]
        parent = self.parent
        while parent is not None:
            full_path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(full_path))