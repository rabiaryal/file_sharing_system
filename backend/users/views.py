from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from .serializers import (
    GoogleLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import build_tokens_for_user, clear_token_cookies, get_refresh_token, set_token_cookies, blacklist_refresh_token
from .models import CustomUser


class RegisterView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=RegisterSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response(
            {
                "message": "User created successfully",
                "user": UserSerializer(user).data,
                "tokens": build_tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )
        return set_token_cookies(response, response.data["tokens"])


class LoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        response = Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "tokens": build_tokens_for_user(user),
            },
            status=status.HTTP_200_OK,
        )
        return set_token_cookies(response, response.data["tokens"])


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh") or get_refresh_token(request)
        if refresh_token:
            blacklist_refresh_token(refresh_token)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return clear_token_cookies(response)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response({"user": UserSerializer(request.user).data}, status=status.HTTP_200_OK)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=GoogleLoginSerializer, responses={200: {'properties': {'access': {'type': 'string'}, 'refresh': {'type': 'string'}, 'user': {'type': 'object'}}, 'type': 'object'}})
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        idinfo = serializer.context.get('idinfo')
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        # Get or create user
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_email_verified': True,  # Google verified email
            }
        )

        if not created:
            # Keep existing accounts in sync with Google profile data.
            user.first_name = first_name
            user.last_name = last_name
            user.is_email_verified = True
            user.save(update_fields=['first_name', 'last_name', 'is_email_verified'])
        
        response = Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "tokens": build_tokens_for_user(user),
            },
            status=status.HTTP_200_OK,
        )
        return set_token_cookies(response, response.data["tokens"])