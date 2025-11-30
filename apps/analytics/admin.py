from django.contrib import admin
from analytics.models.analytics import Analytic, AnalyticDimension, AnalyticDimensionValue


# ======================================================
# AnalyticDimensionValue — READ-ONLY
# ======================================================
@admin.register(AnalyticDimensionValue)
class AnalyticDimensionValueAdmin(admin.ModelAdmin):
    list_display = (
        "dimension",
        "dimension_value",
        "total_value",
        "percentage",
        "computed_at",
    )
    search_fields = ("dimension_value", "dimension__name",
                     "dimension__analytic__name")
    list_filter = ("dimension__analytic__name", "dimension__name")
    readonly_fields = (
        "dimension",
        "dimension_value",
        "total_value",
        "percentage",
        "computed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# ======================================================
# Inline Dimension Editor for Analytic
# ======================================================


class AnalyticDimensionInline(admin.TabularInline):
    model = AnalyticDimension
    extra = 0
    fields = ("name", "label", "source_identifier", "is_active")
    readonly_fields = ()
    show_change_link = True


# ======================================================
# Analytic Admin
# ======================================================
@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "portfolio",
        "value_identifier",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "label", "portfolio__profile__user__email")
    list_filter = ("is_active", "portfolio")
    ordering = ("portfolio", "name")

    inlines = [AnalyticDimensionInline]

    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": ("portfolio", "name", "label", "description"),
        }),
        ("Computation", {
            "fields": ("value_identifier",),
        }),
        ("Meta", {
            "fields": ("is_active", "created_at"),
        }),
    )

# ======================================================
# AnalyticDimension Admin (optional direct editor)
# ======================================================


@admin.register(AnalyticDimension)
class AnalyticDimensionAdmin(admin.ModelAdmin):
    list_display = (
        "analytic",
        "name",
        "label",
        "source_identifier",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "label", "analytic__name")
    list_filter = ("analytic", "is_active")
    ordering = ("analytic", "name")

    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": ("analytic", "name", "label", "description"),
        }),
        ("Mapping", {
            "fields": ("source_identifier",),
        }),
        ("Meta", {
            "fields": ("is_active", "created_at"),
        }),
    )
