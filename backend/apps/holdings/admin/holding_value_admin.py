from django.contrib import admin

from apps.holdings.models import HoldingFactDefinition, HoldingFactValue, HoldingOverride


@admin.register(HoldingFactDefinition)
class HoldingFactDefinitionAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "portfolio", "data_type", "is_active", "created_at", "updated_at")
    list_filter = ("data_type", "is_active", "portfolio")
    search_fields = ("key", "label", "portfolio__name", "portfolio__profile__user__email")
    ordering = ("portfolio", "label", "key")


@admin.register(HoldingFactValue)
class HoldingFactValueAdmin(admin.ModelAdmin):
    list_display = ("definition", "holding", "value", "created_at", "updated_at")
    list_filter = ("definition__portfolio", "definition__data_type")
    search_fields = (
        "definition__key",
        "definition__label",
        "holding__asset__name",
        "holding__asset__symbol",
        "holding__container__portfolio__profile__user__email",
    )
    ordering = ("definition", "holding")


@admin.register(HoldingOverride)
class HoldingOverrideAdmin(admin.ModelAdmin):
    list_display = ("key", "holding", "data_type", "value", "created_at", "updated_at")
    list_filter = ("data_type", "holding__container__portfolio")
    search_fields = (
        "key",
        "holding__asset__name",
        "holding__asset__symbol",
        "holding__container__portfolio__profile__user__email",
    )
    ordering = ("holding", "key")
