from django.contrib import admin
from analytics.models.analytics import (
    Analytic,
    AnalyticDimension,
    AnalyticDimensionValue,
)
from django.utils.html import format_html


# ============================================================
# Inline: AnalyticDimensionValue (READ-ONLY)
# ============================================================
class AnalyticDimensionValueInline(admin.TabularInline):
    model = AnalyticDimensionValue
    extra = 0
    can_delete = False

    readonly_fields = (
        "dimension_value",
        "total_value",
        "percentage",
        "computed_at",
    )

    fields = (
        "dimension_value",
        "total_value",
        "percentage",
        "computed_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ============================================================
# Inline: AnalyticDimension
# ============================================================
class AnalyticDimensionInline(admin.StackedInline):
    model = AnalyticDimension
    extra = 0
    can_delete = True
    show_change_link = True

    fields = (
        "name",
        "label",
        "description",
        "is_active",
        "created_at",
    )
    readonly_fields = ("created_at",)


# ============================================================
# Analytic Admin
# ============================================================
@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "profile",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "profile")
    search_fields = ("name", "label", "profile__user__email")

    inlines = [AnalyticDimensionInline]

    readonly_fields = ("created_at",)


# ============================================================
# AnalyticDimension Admin
# (Allows user to see dimension values in this view)
# ============================================================
@admin.register(AnalyticDimension)
class AnalyticDimensionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "analytic",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "label", "analytic__name")
    list_filter = ("analytic", "is_active")

    readonly_fields = ("created_at",)

    inlines = [AnalyticDimensionValueInline]


# ============================================================
# AnalyticDimensionValue Admin (read-only global view)
# ============================================================
@admin.register(AnalyticDimensionValue)
class AnalyticDimensionValueAdmin(admin.ModelAdmin):
    list_display = (
        "dimension",
        "dimension_value",
        "total_value",
        "percentage",
        "computed_at",
    )
    list_filter = ("dimension",)
    search_fields = ("dimension_value",)

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
