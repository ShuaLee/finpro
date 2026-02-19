from django.urls import path

from allocations.views import (
    AllocationDimensionDetailView,
    AllocationDimensionListCreateView,
    AllocationPlanDetailView,
    AllocationPlanListCreateView,
    AllocationScenarioDetailView,
    AllocationScenarioEvaluateView,
    AllocationScenarioLatestResultsView,
    AllocationScenarioListCreateView,
    AllocationScenarioSetDefaultView,
    AllocationTargetDetailView,
    AllocationTargetListCreateView,
)

urlpatterns = [
    path("plans/", AllocationPlanListCreateView.as_view(), name="allocation-plan-list-create"),
    path("plans/<int:plan_id>/", AllocationPlanDetailView.as_view(), name="allocation-plan-detail"),
    path("plans/<int:plan_id>/scenarios/", AllocationScenarioListCreateView.as_view(), name="allocation-scenario-list-create"),
    path("scenarios/<int:scenario_id>/", AllocationScenarioDetailView.as_view(), name="allocation-scenario-detail"),
    path("scenarios/<int:scenario_id>/set-default/", AllocationScenarioSetDefaultView.as_view(), name="allocation-scenario-set-default"),
    path("scenarios/<int:scenario_id>/evaluate/", AllocationScenarioEvaluateView.as_view(), name="allocation-scenario-evaluate"),
    path("scenarios/<int:scenario_id>/results/latest/", AllocationScenarioLatestResultsView.as_view(), name="allocation-scenario-results-latest"),
    path("scenarios/<int:scenario_id>/dimensions/", AllocationDimensionListCreateView.as_view(), name="allocation-dimension-list-create"),
    path("dimensions/<int:dimension_id>/", AllocationDimensionDetailView.as_view(), name="allocation-dimension-detail"),
    path("dimensions/<int:dimension_id>/targets/", AllocationTargetListCreateView.as_view(), name="allocation-target-list-create"),
    path("targets/<int:target_id>/", AllocationTargetDetailView.as_view(), name="allocation-target-detail"),
]
