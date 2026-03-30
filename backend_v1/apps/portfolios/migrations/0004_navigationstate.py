from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_initial"),
        ("portfolios", "0003_dashboardlayoutstate"),
    ]

    operations = [
        migrations.CreateModel(
            name="NavigationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=120)),
                ("section_order", models.JSONField(blank=True, default=list)),
                ("asset_item_order", models.JSONField(blank=True, default=list)),
                ("account_item_order", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="navigation_states", to="profiles.profile")),
            ],
        ),
        migrations.AddIndex(
            model_name="navigationstate",
            index=models.Index(fields=["profile", "scope"], name="portfolios_n_profile_5f90e4_idx"),
        ),
        migrations.AddConstraint(
            model_name="navigationstate",
            constraint=models.UniqueConstraint(fields=("profile", "scope"), name="uniq_navigation_state_profile_scope"),
        ),
    ]
