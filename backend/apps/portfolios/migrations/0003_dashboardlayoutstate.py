from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_initial"),
        ("portfolios", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardLayoutState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=120)),
                ("active_layout_id", models.CharField(default="default", max_length=100)),
                ("layouts", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="dashboard_layout_states", to="profiles.profile")),
            ],
        ),
        migrations.AddIndex(
            model_name="dashboardlayoutstate",
            index=models.Index(fields=["profile", "scope"], name="portfolios_d_profile_36089e_idx"),
        ),
        migrations.AddConstraint(
            model_name="dashboardlayoutstate",
            constraint=models.UniqueConstraint(fields=("profile", "scope"), name="uniq_dashboard_layout_state_profile_scope"),
        ),
    ]
