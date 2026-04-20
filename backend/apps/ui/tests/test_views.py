from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class DashboardLayoutStateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="dashboard-layout@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)

    def test_get_empty_dashboard_layout_state(self):
        response = self.client.get(reverse("ui-dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"], "dashboards")
        self.assertEqual(response.data["active_layout_id"], "")
        self.assertEqual(response.data["layouts"], [])

    def test_put_then_get_dashboard_layout_state(self):
        payload = {
            "scope": "dashboards",
            "active_layout_id": "layout_main",
            "layouts": [
                {
                    "id": "layout_main",
                    "name": "Main",
                    "viewportLayouts": {
                        "desktop": {"tiles": [{"id": 1, "slot": 2, "colSpan": 3, "rowSpan": 2}]},
                    },
                },
            ],
        }

        put_response = self.client.put(reverse("ui-dashboard-layout-state"), payload, format="json")
        get_response = self.client.get(reverse("ui-dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["active_layout_id"], "layout_main")
        self.assertEqual(get_response.data["layouts"], payload["layouts"])

    def test_dashboard_layout_state_is_user_scoped(self):
        payload = {
            "scope": "dashboards",
            "active_layout_id": "layout_main",
            "layouts": [{"id": "layout_main", "name": "Main"}],
        }
        self.client.put(reverse("ui-dashboard-layout-state"), payload, format="json")

        other_user = get_user_model().objects.create_user(
            email="other-dashboard-layout@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(other_user)
        response = self.client.get(reverse("ui-dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_layout_id"], "")
        self.assertEqual(response.data["layouts"], [])


class NavigationStateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="navigation-state@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)

    def test_get_empty_navigation_state(self):
        response = self.client.get(reverse("ui-navigation-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"], "dashboards")
        self.assertEqual(response.data["section_order"], [])
        self.assertEqual(response.data["asset_item_order"], [])
        self.assertEqual(response.data["account_item_order"], [])
        self.assertEqual(response.data["asset_types_collapsed"], False)
        self.assertEqual(response.data["accounts_collapsed"], False)
        self.assertEqual(response.data["active_item_key"], "")

    def test_put_then_get_navigation_state(self):
        payload = {
            "scope": "dashboards",
            "section_order": ["portfolio", "assets", "accounts"],
            "asset_item_order": ["asset:a", "asset:b"],
            "account_item_order": ["account:1"],
            "asset_types_collapsed": True,
            "accounts_collapsed": False,
            "active_item_key": "asset:a",
        }

        put_response = self.client.put(reverse("ui-navigation-state"), payload, format="json")
        get_response = self.client.get(reverse("ui-navigation-state"), {"scope": "dashboards"})

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["section_order"], payload["section_order"])
        self.assertEqual(get_response.data["asset_item_order"], payload["asset_item_order"])
        self.assertEqual(get_response.data["account_item_order"], payload["account_item_order"])
        self.assertEqual(get_response.data["asset_types_collapsed"], True)
        self.assertEqual(get_response.data["accounts_collapsed"], False)
        self.assertEqual(get_response.data["active_item_key"], "asset:a")

    def test_navigation_state_is_user_scoped(self):
        payload = {
            "scope": "dashboards",
            "section_order": ["portfolio"],
            "asset_item_order": [],
            "account_item_order": [],
            "asset_types_collapsed": True,
            "accounts_collapsed": True,
            "active_item_key": "portfolio",
        }
        self.client.put(reverse("ui-navigation-state"), payload, format="json")

        other_user = get_user_model().objects.create_user(
            email="other-navigation-state@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(other_user)
        response = self.client.get(reverse("ui-navigation-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["section_order"], [])
        self.assertEqual(response.data["asset_types_collapsed"], False)
        self.assertEqual(response.data["accounts_collapsed"], False)
