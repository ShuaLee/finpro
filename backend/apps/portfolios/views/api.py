from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assets.models import Asset
from fx.models import FXCurrency
from portfolios.models import Portfolio, PortfolioDenomination
from portfolios.serializers import (
    PortfolioDenominationCreateSerializer,
    PortfolioDenominationPatchSerializer,
    PortfolioDenominationSerializer,
    PortfolioValuationSnapshotSerializer,
)
from portfolios.services import PortfolioValuationService


def _owned_portfolio_or_404(*, portfolio_id: int, user):
    return get_object_or_404(
        Portfolio.objects.select_related("profile__currency"),
        id=portfolio_id,
        profile__user=user,
    )


def _owned_denomination_or_404(*, denomination_id: int, user):
    return get_object_or_404(
        PortfolioDenomination.objects.select_related("portfolio__profile"),
        id=denomination_id,
        portfolio__profile__user=user,
    )


class PortfolioValuationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id: int):
        portfolio = _owned_portfolio_or_404(portfolio_id=portfolio_id, user=request.user)
        identifier = request.query_params.get("identifier", "current_value")
        payload = PortfolioValuationService.valuation_payload(
            portfolio=portfolio,
            identifier=identifier,
        )
        return Response(payload, status=status.HTTP_200_OK)


class PortfolioValuationSnapshotCaptureView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, portfolio_id: int):
        portfolio = _owned_portfolio_or_404(portfolio_id=portfolio_id, user=request.user)
        identifier = request.data.get("identifier", "current_value")
        snapshot = PortfolioValuationService.capture_snapshot(
            portfolio=portfolio,
            identifier=identifier,
        )
        return Response(
            PortfolioValuationSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )


class PortfolioValuationSnapshotListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id: int):
        portfolio = _owned_portfolio_or_404(portfolio_id=portfolio_id, user=request.user)
        snapshots = portfolio.valuation_snapshots.all()[:50]
        return Response(
            PortfolioValuationSnapshotSerializer(snapshots, many=True).data,
            status=status.HTTP_200_OK,
        )


class PortfolioDenominationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id: int):
        portfolio = _owned_portfolio_or_404(portfolio_id=portfolio_id, user=request.user)
        PortfolioValuationService.ensure_default_denominations(portfolio=portfolio)
        rows = portfolio.denominations.order_by("display_order", "key")
        return Response(PortfolioDenominationSerializer(rows, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, portfolio_id: int):
        portfolio = _owned_portfolio_or_404(portfolio_id=portfolio_id, user=request.user)
        serializer = PortfolioDenominationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        currency = None
        if data.get("currency_code"):
            currency = get_object_or_404(FXCurrency, code=data["currency_code"].upper(), is_active=True)

        asset = None
        if data.get("asset_id"):
            asset = get_object_or_404(Asset, id=data["asset_id"])

        row = PortfolioDenomination(
            portfolio=portfolio,
            key=data["key"],
            label=data["label"],
            kind=data["kind"],
            currency=currency,
            asset=asset,
            reference_code=(data.get("reference_code") or "").strip() or None,
            unit_label=(data.get("unit_label") or "").strip() or None,
            display_order=data.get("display_order", 0),
            is_active=data.get("is_active", True),
            is_system=False,
        )

        try:
            row.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PortfolioDenominationSerializer(row).data, status=status.HTTP_201_CREATED)


class PortfolioDenominationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, denomination_id: int):
        row = _owned_denomination_or_404(denomination_id=denomination_id, user=request.user)
        serializer = PortfolioDenominationPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "currency_code" in data:
            row.currency = get_object_or_404(FXCurrency, code=data["currency_code"].upper(), is_active=True)
        if "asset_id" in data:
            row.asset = get_object_or_404(Asset, id=data["asset_id"])
        if "reference_code" in data:
            row.reference_code = (data.get("reference_code") or "").strip() or None
        if "unit_label" in data:
            row.unit_label = (data.get("unit_label") or "").strip() or None

        for field in ("label", "display_order", "is_active"):
            if field in data:
                setattr(row, field, data[field])

        try:
            row.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PortfolioDenominationSerializer(row).data, status=status.HTTP_200_OK)

    def delete(self, request, denomination_id: int):
        row = _owned_denomination_or_404(denomination_id=denomination_id, user=request.user)
        try:
            row.delete()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
