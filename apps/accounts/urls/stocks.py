from django.urls import path
from accounts.views.stocks import (
    SelfManagedAccountListCreateView,
    ManagedAccountListCreateView,
    StockAccountsDashboardView,
    # AddHoldingView,
    # EditColumnValueView
)

urlpatterns = [
    path('self-managed/', SelfManagedAccountListCreateView.as_view(),
         name='self-managed-accounts'),
    path('managed/', ManagedAccountListCreateView.as_view(),
         name='managed-accounts'),
    path('dashboard/', StockAccountsDashboardView.as_view(),
         name='stock-accounts-dashboard'),
    # path('self-managed/<int:account_id>/holdings/', AddHoldingView.as_view(), name='add-holding'),
    # path('self-managed/column-value/<int:value_id>/', EditColumnValueView.as_view(), name='edit-column-value'),
]
