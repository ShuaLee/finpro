from .auth import urlpatterns as auth_urlpatterns
from .profile import urlpatterns as profile_urlpatterns

urlpatterns = [
    *auth_urlpatterns,
    *profile_urlpatterns,
]
