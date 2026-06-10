

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os
from dotenv import load_dotenv
import structlog


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

log = structlog.get_logger(__name__)


load_dotenv()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=RegisterSerializer, responses=UserSerializer)
    def post(self, request):
        log.info("user_registration_attempt")
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log.info("user_registered", user_id=user.id, email=user.email)
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
        log.info("user_login_attempt")
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        log.info("user_login_successful", user_id=user.id, email=user.email)
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
    @extend_schema(request=LogoutSerializer, responses={200: None})
    def post(self, request):
        log.info("user_logout_attempt", user_id=request.user.id)
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh") or get_refresh_token(request)
        if refresh_token:
            blacklist_refresh_token(refresh_token)

        user = request.user
        user_id = user.id

        # 1. Clean up user files in Supabase storage
        from files.models import CompressedPDF
        from files.services import get_supabase_client
        pdfs = CompressedPDF.objects.filter(user=user)
        if pdfs.exists():
            try:
                client = get_supabase_client()
                bucket = client.storage.from_(os.getenv("SUPABASE_BUCKET", "public"))
                for pdf in pdfs:
                    raw_path = pdf.storage_path
                    try:
                        bucket.remove([raw_path])
                    except Exception as storage_err:
                        log.warning("supabase_file_deletion_failed_on_logout", path=raw_path, error=str(storage_err))
            except Exception as e:
                log.error("failed_to_initialize_supabase_on_logout", user_id=user_id, error=str(e))

        # 2. Delete user record (cascades to delete CompressedPDF and ShareLink in DB)
        user.delete()
        log.info("user_logout_and_deleted_successful", user_id=user_id)

        response = Response(
            {"message": "Logout successful. User details deleted. Make sure to share your links!"},
            status=status.HTTP_200_OK
        )
        return clear_token_cookies(response)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        log.info("user_profile_requested", user_id=request.user.id)
        return Response({"user": UserSerializer(request.user).data}, status=status.HTTP_200_OK)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        log.info("user_profile_update_attempt", user_id=request.user.id)
        serializer = ProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log.info("user_profile_updated", user_id=request.user.id)
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=GoogleLoginSerializer, responses={200: {'properties': {'access': {'type': 'string'}, 'refresh': {'type': 'string'}, 'user': {'type': 'object'}}, 'type': 'object'}})
    def post(self, request):
        log.info("google_login_attempt")
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

        if created:
            log.info("google_user_created", user_id=user.id, email=email)
        else:
            # Keep existing accounts in sync with Google profile data.
            user.first_name = first_name
            user.last_name = last_name
            user.is_email_verified = True
            user.save(update_fields=['first_name', 'last_name', 'is_email_verified'])
            log.info("google_user_synced", user_id=user.id, email=email)

        log.info("google_login_successful", user_id=user.id, email=email)

        response = Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "tokens": build_tokens_for_user(user),
            },
            status=status.HTTP_200_OK,
        )
        return set_token_cookies(response, response.data["tokens"])
    

   

class MongoHealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            db = client[os.getenv("MONGO_LOG_DB", "file_sharing_logs")]
            stats = db.command("dbstats")
            return Response({
                "status": "connected",
                "database": os.getenv("MONGO_LOG_DB", "file_sharing_logs"),
                "collections": stats.get("collections", 0),
                "objects": stats.get("objects", 0),
            }, status=status.HTTP_200_OK)
        except ServerSelectionTimeoutError as e:
            return Response({
                "status": "disconnected",
                "error": str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)