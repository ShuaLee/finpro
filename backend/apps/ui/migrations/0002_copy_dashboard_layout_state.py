from django.db import migrations


def copy_dashboard_layout_state(apps, schema_editor):
    OldDashboardLayoutState = apps.get_model("holdings", "DashboardLayoutState")
    NewDashboardLayoutState = apps.get_model("ui", "DashboardLayoutState")

    for old_state in OldDashboardLayoutState.objects.all().iterator():
        NewDashboardLayoutState.objects.update_or_create(
            profile_id=old_state.profile_id,
            scope=old_state.scope,
            defaults={
                "active_layout_id": old_state.active_layout_id,
                "layouts": old_state.layouts,
                "created_at": old_state.created_at,
                "updated_at": old_state.updated_at,
            },
        )


def reverse_copy_dashboard_layout_state(apps, schema_editor):
    OldDashboardLayoutState = apps.get_model("holdings", "DashboardLayoutState")
    NewDashboardLayoutState = apps.get_model("ui", "DashboardLayoutState")

    for new_state in NewDashboardLayoutState.objects.all().iterator():
        OldDashboardLayoutState.objects.update_or_create(
            profile_id=new_state.profile_id,
            scope=new_state.scope,
            defaults={
                "active_layout_id": new_state.active_layout_id,
                "layouts": new_state.layouts,
                "created_at": new_state.created_at,
                "updated_at": new_state.updated_at,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("holdings", "0003_dashboardlayoutstate"),
        ("ui", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(copy_dashboard_layout_state, reverse_copy_dashboard_layout_state),
    ]
