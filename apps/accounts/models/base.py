from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ForeignKey, OneToOneField
from schemas.models import SchemaColumnVisibility


class BaseAccount(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def get_active_schema(self):
        """
        Resolve the active schema for this account via its parent sub-portfolio.
        Works across all asset types.
        """
        subportfolio = getattr(self, "sub_portfolio", None)
        if not subportfolio:
            raise RuntimeError(
                f"{self.__class__.__name__} has no `sub_portfolio` property defined."
            )

        return subportfolio.get_schema_for_account_model(self.__class__)

    def get_profile(self):
        """
        Return the Profile that owns this account via its sub-portfolio.
        We look for any FK/O2O on this model whose target is a subclass of
        portfolios.models.base.BaseAssetPortfolio, then hop:
            <subportfolio>.portfolio.profile
        """
        for field in self._meta.get_fields():
            if isinstance(field, (ForeignKey, OneToOneField)):
                rel_model = getattr(field, "remote_field", None)
                rel_model = getattr(rel_model, "model", None)
                if not rel_model:
                    continue
                # Heuristic: a sub-portfolio has a 'portfolio' FK/O2O to portfolios.Portfolio
                if hasattr(rel_model, "portfolio"):
                    sp = getattr(self, field.name, None)
                    if sp is not None and getattr(sp, "portfolio", None):
                        return sp.portfolio.profile
        return None

    def derive_profile_currency(self):
        prof = self.get_profile()
        return getattr(prof, "currency", None) if prof else None

    def initialize_visibility_settings(self, schema):
        """
        Sets up SchemaColumnVisibility rows for this account based on the given schema.
        Should be called once, right after account creation.
        """
        ct = ContentType.objects.get_for_model(self.__class__)
        for column in schema.columns.all():
            SchemaColumnVisibility.objects.get_or_create(
                content_type=ct,
                object_id=self.id,
                column=column,
                defaults={'is_visible': True}
            )

    def get_visible_columns(self):
        """
        Returns visible SchemaColumns for this account.
        """
        ct = ContentType.objects.get_for_model(self.__class__)
        return SchemaColumnVisibility.objects.filter(
            content_type=ct,
            object_id=self.id,
            is_visible=True
        ).select_related("column")
