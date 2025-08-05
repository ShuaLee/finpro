from django.urls import path
from accounts.views.stocks import (
    SelfManagedAccountListCreateView,
    SelfManagedAccountDetailView,
    ManagedAccountListCreateView,
    ManagedAccountDetailView,
    StockAccountsDashboardView,
    AddHoldingView,
    # EditColumnValueView
)

urlpatterns = [
    path('self-managed/', SelfManagedAccountListCreateView.as_view(),
         name='self-managed-accounts'),
    path('self-managed/<int:pk>/', SelfManagedAccountDetailView.as_view(),
         name='self-managed-detail'),
    path('managed/', ManagedAccountListCreateView.as_view(),
         name='managed-accounts'),
    path('managed/<int:pk>/', ManagedAccountDetailView.as_view(),
         name='managed-detail'),
    path('dashboard/', StockAccountsDashboardView.as_view(),
         name='stock-accounts-dashboard'),
    path('self-managed/<int:account_id>/holdings/',
         AddHoldingView.as_view(), name='add-holding'),
    # path('self-managed/column-value/<int:value_id>/', EditColumnValueView.as_view(), name='edit-column-value'),
]
