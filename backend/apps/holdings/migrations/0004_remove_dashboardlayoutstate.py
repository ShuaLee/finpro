from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("holdings", "0003_dashboardlayoutstate"),
        ("ui", "0002_copy_dashboard_layout_state"),
    ]

    operations = [
        migrations.DeleteModel(
            name="DashboardLayoutState",
        ),
    ]
