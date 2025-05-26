"""
from django.http import HttpResponseRedirect

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if not request.user.profile.profile_setup_complete:
                # Allow access to profile endpoint and logout
                if not request.path.startswith('/api/profile/') and not request.path.startswith('/api/auth/logout/'):
                    return HttpResponseRedirect('/profile/setup')
        return self.get_response(request)
"""