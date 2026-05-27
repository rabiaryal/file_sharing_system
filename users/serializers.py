from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser

from .services import blacklist_refresh_token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            username=data["email"],
            password=data["password"],
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("This account is disabled")

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "profile_picture",
            "is_email_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_email_verified",
            "created_at",
            "updated_at",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone", "profile_picture"]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def save(self, **kwargs):
        refresh_token = self.validated_data["refresh"]
        blacklist_refresh_token(refresh_token)


class GoogleLoginSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
            import os
            
            google_client_id = os.getenv('GOOGLE_CLIENT_ID')
            if not google_client_id:
                raise serializers.ValidationError("Google client ID not configured")
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(value, requests.Request(), google_client_id)
            
            # Token is valid, store it for later use
            self.context['idinfo'] = idinfo
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Invalid Google token: {str(e)}")