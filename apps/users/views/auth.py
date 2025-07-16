"""
users.views.auth
~~~~~~~~~~~~~~~~
Handles authentication-related API endpoints:
- User signup completion
- Cookie-based login, logout
- Token refresh
"""

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from users.serializers import SignupSerializer
import logging

logger = logging.getLogger(__name__)


class SignupView(generics.CreateAPIView):
    """
    Completes the signup process by creating a user and returning JWT tokens.

    Workflow:
    - Validates user data via serializer
    - Creates the user and initializes Profile + Portfolio
    - Returns JWT tokens (access & refresh)
    """
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Creates user + initializes profile

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            "detail": "Signup successful",
            "user": {"id": user.id, "email": user.email}
        }, status=status.HTTP_201_CREATED)

        response.set_cookie("access", str(refresh.access_token),
                            httponly=True, secure=True, samesite="Lax", max_age=60 * 5)
        response.set_cookie("refresh", str(refresh),
                            httponly=True, secure=True, samesite="Lax", max_age=60 * 60 * 24 * 7)
        return response
    
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    """
    Provides a CSRF token cookie for secure POST requests.
    Frontend should call this before any login/signup action.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({"detail": "CSRF cookie set"})


class CookieLoginView(APIView):
    """
    Handles user login and sets JWT tokens in HttpOnly cookies.

    - Validates credentials using Django's authenticate()
    - Returns response with JWT tokens stored in cookies

    Requires CSRF protection.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Authenticate user
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate tokens and set as cookies
        refresh = RefreshToken.for_user(user)

        response = Response({"detail": "Login successful"},
                            status=status.HTTP_200_OK)
        response = Response({"detail": "Login successful"}, status=status.HTTP_200_OK)

        response.set_cookie("access", str(refresh.access_token),
                            httponly=True, secure=True, samesite="Lax", max_age=60 * 5)
        response.set_cookie("refresh", str(refresh),
                            httponly=True, secure=True, samesite="Lax", max_age=60 * 60 * 24 * 7)
        return response



class CookieLogoutView(APIView):
    """
    Logs out the user by clearing JWT cookies.
    Requires CSRF protection.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Logged out"},
                            status=status.HTTP_200_OK)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class CookieRefreshView(APIView):
    """
    Issues a new access token using the refresh token.
    Does NOT require access token (AllowAny).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"detail": "No refresh token provided"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except InvalidToken:
            return Response({"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie("access", access_token,
                            httponly=True, secure=True, samesite="Lax", max_age=60 * 5)
        return response

