from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import AccountType
from allocations.models import (
    AllocationDimension,
    AllocationGapResult,
    AllocationPlan,
    AllocationScenario,
    AllocationTarget,
)
from allocations.serializers import (
    AllocationDimensionCreateSerializer,
    AllocationDimensionPatchSerializer,
    AllocationDimensionSerializer,
    AllocationEvaluationRunSerializer,
    AllocationGapResultSerializer,
    AllocationPlanCreateSerializer,
    AllocationPlanPatchSerializer,
    AllocationPlanSerializer,
    AllocationScenarioCreateSerializer,
    AllocationScenarioPatchSerializer,
    AllocationScenarioSerializer,
    AllocationTargetCreateSerializer,
    AllocationTargetPatchSerializer,
    AllocationTargetSerializer,
)
from allocations.services.engine import AllocationEngine
from portfolios.models import Portfolio


def _owned_plan_or_404(*, plan_id: int, user):
    return get_object_or_404(
        AllocationPlan.objects.select_related("portfolio__profile"),
        id=plan_id,
        portfolio__profile__user=user,
    )


def _owned_scenario_or_404(*, scenario_id: int, user):
    return get_object_or_404(
        AllocationScenario.objects.select_related("plan__portfolio__profile"),
        id=scenario_id,
        plan__portfolio__profile__user=user,
    )


def _owned_dimension_or_404(*, dimension_id: int, user):
    return get_object_or_404(
        AllocationDimension.objects.select_related("scenario__plan__portfolio__profile"),
        id=dimension_id,
        scenario__plan__portfolio__profile__user=user,
    )


def _owned_target_or_404(*, target_id: int, user):
    return get_object_or_404(
        AllocationTarget.objects.select_related("dimension__scenario__plan__portfolio__profile"),
        id=target_id,
        dimension__scenario__plan__portfolio__profile__user=user,
    )


class AllocationPlanListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = (
            AllocationPlan.objects.filter(portfolio__profile__user=request.user)
            .prefetch_related("scenarios")
            .order_by("portfolio_id", "name")
        )
        return Response(AllocationPlanSerializer(plans, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AllocationPlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        portfolio = get_object_or_404(
            Portfolio,
            id=serializer.validated_data["portfolio_id"],
            profile__user=request.user,
        )

        account_type = None
        account_type_id = serializer.validated_data.get("account_type_id")
        if account_type_id:
            account_type = get_object_or_404(AccountType, id=account_type_id)

        plan = AllocationPlan(
            portfolio=portfolio,
            name=serializer.validated_data["name"],
            label=serializer.validated_data["label"],
            description=serializer.validated_data.get("description"),
            base_value_identifier=serializer.validated_data.get("base_value_identifier", "current_value"),
            base_scope=serializer.validated_data.get("base_scope", AllocationPlan.BaseScope.TOTAL_PORTFOLIO),
            account_type=account_type,
            is_active=True,
        )

        try:
            plan.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class AllocationPlanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id: int):
        plan = _owned_plan_or_404(plan_id=plan_id, user=request.user)
        return Response(AllocationPlanSerializer(plan).data, status=status.HTTP_200_OK)

    def patch(self, request, plan_id: int):
        plan = _owned_plan_or_404(plan_id=plan_id, user=request.user)
        serializer = AllocationPlanPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        if "account_type_id" in data:
            account_type_id = data.pop("account_type_id")
            plan.account_type = get_object_or_404(AccountType, id=account_type_id) if account_type_id else None

        for field, value in data.items():
            setattr(plan, field, value)

        try:
            plan.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationPlanSerializer(plan).data, status=status.HTTP_200_OK)

    def delete(self, request, plan_id: int):
        plan = _owned_plan_or_404(plan_id=plan_id, user=request.user)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllocationScenarioListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id: int):
        plan = _owned_plan_or_404(plan_id=plan_id, user=request.user)
        scenarios = plan.scenarios.prefetch_related("dimensions").order_by("name")
        return Response(AllocationScenarioSerializer(scenarios, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, plan_id: int):
        plan = _owned_plan_or_404(plan_id=plan_id, user=request.user)
        serializer = AllocationScenarioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scenario = AllocationScenario(
            plan=plan,
            name=serializer.validated_data["name"],
            label=serializer.validated_data["label"],
            description=serializer.validated_data.get("description"),
            is_default=serializer.validated_data.get("is_default", False),
            is_active=serializer.validated_data.get("is_active", True),
        )

        try:
            scenario.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationScenarioSerializer(scenario).data, status=status.HTTP_201_CREATED)


class AllocationScenarioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        return Response(AllocationScenarioSerializer(scenario).data, status=status.HTTP_200_OK)

    def patch(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        serializer = AllocationScenarioPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(scenario, field, value)

        try:
            scenario.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationScenarioSerializer(scenario).data, status=status.HTTP_200_OK)

    def delete(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        scenario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllocationScenarioSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        AllocationScenario.objects.filter(plan=scenario.plan, is_default=True).exclude(id=scenario.id).update(is_default=False)
        scenario.is_default = True

        try:
            scenario.save(update_fields=["is_default", "updated_at"])
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationScenarioSerializer(scenario).data, status=status.HTTP_200_OK)


class AllocationDimensionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        dimensions = scenario.dimensions.prefetch_related("targets").all()
        return Response(AllocationDimensionSerializer(dimensions, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        serializer = AllocationDimensionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dimension = AllocationDimension(
            scenario=scenario,
            name=serializer.validated_data["name"],
            label=serializer.validated_data["label"],
            description=serializer.validated_data.get("description"),
            source_identifier=serializer.validated_data["source_identifier"],
            source_analytic_name=serializer.validated_data.get("source_analytic_name") or None,
            denominator_mode=serializer.validated_data.get("denominator_mode", AllocationDimension.DenominatorMode.BASE_SCOPE_TOTAL),
            is_active=serializer.validated_data.get("is_active", True),
            display_order=serializer.validated_data.get("display_order", 0),
        )

        try:
            dimension.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationDimensionSerializer(dimension).data, status=status.HTTP_201_CREATED)


class AllocationDimensionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        serializer = AllocationDimensionPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(dimension, field, value if field != "source_analytic_name" else (value or None))

        try:
            dimension.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationDimensionSerializer(dimension).data, status=status.HTTP_200_OK)

    def delete(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        dimension.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllocationTargetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        targets = dimension.targets.order_by("display_order", "key")
        return Response(AllocationTargetSerializer(targets, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        serializer = AllocationTargetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = AllocationTarget(dimension=dimension, **serializer.validated_data)

        try:
            target.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationTargetSerializer(target).data, status=status.HTTP_201_CREATED)


class AllocationTargetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, target_id: int):
        target = _owned_target_or_404(target_id=target_id, user=request.user)
        serializer = AllocationTargetPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(target, field, value)

        try:
            target.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AllocationTargetSerializer(target).data, status=status.HTTP_200_OK)

    def delete(self, request, target_id: int):
        target = _owned_target_or_404(target_id=target_id, user=request.user)
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllocationScenarioEvaluateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        run = AllocationEngine.evaluate(scenario=scenario, triggered_by=request.user)
        return Response(AllocationEvaluationRunSerializer(run).data, status=status.HTTP_201_CREATED)


class AllocationScenarioLatestResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id: int):
        scenario = _owned_scenario_or_404(scenario_id=scenario_id, user=request.user)
        run = scenario.runs.filter(status="success").first()
        if not run:
            return Response({"detail": "No successful allocation evaluation run exists yet."}, status=status.HTTP_404_NOT_FOUND)

        rows = (
            AllocationGapResult.objects.filter(run=run)
            .select_related("dimension", "target")
            .order_by("dimension__display_order", "target__display_order", "bucket_key_snapshot")
        )

        grouped = {}
        for row in rows:
            dim_id = row.dimension_id
            if dim_id not in grouped:
                grouped[dim_id] = {
                    "dimension_id": dim_id,
                    "dimension_name": row.dimension.name if row.dimension else None,
                    "rows": [],
                }
            grouped[dim_id]["rows"].append(AllocationGapResultSerializer(row).data)

        return Response(
            {
                "scenario_id": scenario.id,
                "run": AllocationEvaluationRunSerializer(run).data,
                "dimensions": list(grouped.values()),
            },
            status=status.HTTP_200_OK,
        )
