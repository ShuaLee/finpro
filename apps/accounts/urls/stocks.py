from django.urls import path
from accounts.views.stocks import (
    StockAccountListCreateView,
    StockAccountDetailView,
    StockAccountPartialUpdateView,
    StockAccountSwitchModeView,
    StockAccountsDashboardView,
    AddHoldingView,
)

urlpatterns = [
    # Accounts
    path('', StockAccountListCreateView.as_view(), name='stock-account-list-create'),
    path('<int:pk>/', StockAccountDetailView.as_view(), name='stock-account-detail'),
    path('<int:pk>/update/', StockAccountPartialUpdateView.as_view(), name='stock-account-update'),
    path('<int:pk>/switch_mode/', StockAccountSwitchModeView.as_view(), name='stock-account-switch-mode'),

    # Dashboard
    path('dashboard/', StockAccountsDashboardView.as_view(), name='stock-accounts-dashboard'),

    # Holdings (self-managed only)
    path('<int:account_id>/holdings/', AddHoldingView.as_view(), name='stock-account-add-holding'),
]
