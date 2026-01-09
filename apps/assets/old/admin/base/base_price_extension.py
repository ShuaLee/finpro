from django.contrib import admin
from assets.models.pricing import AssetPrice


class BasePriceExtensionInline(admin.StackedInline):
    """
    Base inline for all price extensions.
    Model must define a OneToOneField to AssetPrice.
    """

    extra = 0
    max_num = 1
    fk_name = "asset_price"   # required so Django doesn't guess incorrectly

    def get_formset(self, request, obj=None, **kwargs):
        """
        Override queryset so Django binds via Asset rather than AssetPrice.
        """
        formset = super().get_formset(request, obj, **kwargs)

        if obj is None:
            formset.queryset = self.model.objects.none()
            return formset

        try:
            price = obj.asset_price
        except AssetPrice.DoesNotExist:
            formset.queryset = self.model.objects.none()
        else:
            formset.queryset = self.model.objects.filter(asset_price=price)

        return formset
