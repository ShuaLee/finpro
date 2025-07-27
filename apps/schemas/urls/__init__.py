# schemas/urls/__init__.py
from django.urls import path, include

urlpatterns = [
    path('stocks/', include('schemas.urls.stocks')),  # Stock-specific routes
    # Future: metals, crypto
]
