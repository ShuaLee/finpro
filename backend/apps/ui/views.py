from typing import Any

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ui.models import DashboardLayoutState, NavigationState
from apps.users.views.base import ServiceAPIView


class DashboardLayoutStateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def _serialize(self, state: DashboardLayoutState | None, scope: str) -> dict[str, Any]:
        return {
            "scope": scope,
            "active_layout_id": state.active_layout_id if state else "",
            "layouts": state.layouts if state else [],
            "updated_at": state.updated_at.isoformat() if state and state.updated_at else None,
        }

    def get(self, request):
        scope = (request.query_params.get("scope") or "dashboards").strip() or "dashboards"
        state = DashboardLayoutState.objects.filter(profile=request.user.profile, scope=scope).first()
        return Response(self._serialize(state, scope))

    def put(self, request):
        scope = str(request.data.get("scope") or "dashboards").strip() or "dashboards"
        active_layout_id = str(request.data.get("active_layout_id") or "")
        layouts = request.data.get("layouts")
        if not isinstance(layouts, list):
            return Response({"layouts": "Expected a list of dashboard layouts."}, status=status.HTTP_400_BAD_REQUEST)

        state, _created = DashboardLayoutState.objects.update_or_create(
            profile=request.user.profile,
            scope=scope,
            defaults={
                "active_layout_id": active_layout_id,
                "layouts": layouts,
            },
        )
        return Response(self._serialize(state, scope))


class NavigationStateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def _serialize(self, state: NavigationState | None, scope: str) -> dict[str, Any]:
        return {
            "scope": scope,
            "section_order": state.section_order if state else [],
            "asset_item_order": state.asset_item_order if state else [],
            "account_item_order": state.account_item_order if state else [],
            "asset_types_collapsed": state.asset_types_collapsed if state else False,
            "accounts_collapsed": state.accounts_collapsed if state else False,
            "active_item_key": state.active_item_key if state else "",
            "updated_at": state.updated_at.isoformat() if state and state.updated_at else None,
        }

    def get(self, request):
        scope = (request.query_params.get("scope") or "dashboards").strip() or "dashboards"
        state = NavigationState.objects.filter(profile=request.user.profile, scope=scope).first()
        return Response(self._serialize(state, scope))

    def put(self, request):
        scope = str(request.data.get("scope") or "dashboards").strip() or "dashboards"
        section_order = request.data.get("section_order")
        asset_item_order = request.data.get("asset_item_order")
        account_item_order = request.data.get("account_item_order")

        if not isinstance(section_order, list):
            return Response({"section_order": "Expected a list of navigation sections."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(asset_item_order, list):
            return Response({"asset_item_order": "Expected a list of asset item keys."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(account_item_order, list):
            return Response({"account_item_order": "Expected a list of account item keys."}, status=status.HTTP_400_BAD_REQUEST)

        state, _created = NavigationState.objects.update_or_create(
            profile=request.user.profile,
            scope=scope,
            defaults={
                "section_order": section_order,
                "asset_item_order": asset_item_order,
                "account_item_order": account_item_order,
                "asset_types_collapsed": bool(request.data.get("asset_types_collapsed", False)),
                "accounts_collapsed": bool(request.data.get("accounts_collapsed", False)),
                "active_item_key": str(request.data.get("active_item_key") or ""),
            },
        )
        return Response(self._serialize(state, scope))
