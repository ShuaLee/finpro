import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0003_profile_country_supportedcountry_supportedcurrency"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardLayoutState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=80)),
                ("active_layout_id", models.CharField(blank=True, max_length=120)),
                ("layouts", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ui_dashboard_layout_states",
                        to="users.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["scope"],
            },
        ),
        migrations.CreateModel(
            name="NavigationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=80)),
                ("section_order", models.JSONField(blank=True, default=list)),
                ("asset_item_order", models.JSONField(blank=True, default=list)),
                ("account_item_order", models.JSONField(blank=True, default=list)),
                ("asset_types_collapsed", models.BooleanField(default=False)),
                ("accounts_collapsed", models.BooleanField(default=False)),
                ("active_item_key", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ui_navigation_states",
                        to="users.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["scope"],
            },
        ),
        migrations.AddConstraint(
            model_name="dashboardlayoutstate",
            constraint=models.UniqueConstraint(
                fields=("profile", "scope"),
                name="uniq_ui_dashboard_layout_state_per_profile_scope",
            ),
        ),
        migrations.AddIndex(
            model_name="dashboardlayoutstate",
            index=models.Index(fields=["profile", "scope"], name="ui_dashboar_profile_dcfb27_idx"),
        ),
        migrations.AddConstraint(
            model_name="navigationstate",
            constraint=models.UniqueConstraint(
                fields=("profile", "scope"),
                name="uniq_ui_navigation_state_per_profile_scope",
            ),
        ),
        migrations.AddIndex(
            model_name="navigationstate",
            index=models.Index(fields=["profile", "scope"], name="ui_navigati_profile_c70359_idx"),
        ),
    ]
