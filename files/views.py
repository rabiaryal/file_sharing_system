from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import throttle_classes
from rest_framework.throttling import AnonRateThrottle
from django.db import models
from django.shortcuts import redirect, render
from drf_spectacular.utils import extend_schema
from .serializers import UploadIntentSerializer, ProcessSerializer
from .services import make_presigned_upload, make_presigned_download
from .models import CompressedPDF, ShareLink
from .secure_links import SimpleLinkEngine
from django.utils import timezone
import os
from datetime import timedelta


class PublicLinkBurstThrottle(AnonRateThrottle):
    rate = os.getenv("SHARE_BURST_RATE", "5/minute")


def _resolve_active_path(pdf: CompressedPDF) -> str:
    if pdf.status == "COMPLETED" and pdf.compressed_size:
        return pdf.storage_path.replace("raw/", "compressed/")
    return pdf.storage_path

class UploadIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(request=UploadIntentSerializer, responses=200)
    def post(self, request):
        serializer = UploadIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filename = serializer.validated_data["filename"]
        size = serializer.validated_data["size"]

        # simple quota check (per-user) - sum compressed sizes
        total = CompressedPDF.objects.filter(user=request.user).aggregate(total=models.Sum("compressed_size"))
        used = total.get("total") or 0
        if used + size > 1_000_000_000:  # 1GB
            return Response({"detail": "User storage limit exceeded"}, status=status.HTTP_403_FORBIDDEN)

        path = f"raw/{request.user.id}/{int(timezone.now().timestamp())}_{filename}"
        presigned = make_presigned_upload(path)
        return Response(
            {
                "storage_path": path,
                "upload_url": presigned.get("upload_url")
            },
            status=status.HTTP_200_OK
        )


class ProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(request=ProcessSerializer, responses=201)
    def post(self, request):
        serializer = ProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        storage_path = serializer.validated_data["storage_path"]
        original_name = serializer.validated_data["original_name"]
        original_size = serializer.validated_data["original_size"]
        expires_in = serializer.validated_data.get("expires_in_seconds", 86400)

        record = CompressedPDF.objects.create(
            user=request.user,
            original_name=original_name,
            storage_path=storage_path,
            original_size=original_size,
            status="PROCESSING",
        )

        # enqueue Celery task
        from .tasks import compress_pdf_task
        compress_pdf_task.delay(record.id)

        # create share link metadata (without token - token is generated on-demand)
        share_link = ShareLink.objects.create(
            pdf_record=record,
            expires_at=timezone.now() + timedelta(seconds=expires_in),
        )

        # Generate stateless HMAC-based token using file_id and expiry
        token = SimpleLinkEngine.generate_token(record.id, execution_window_seconds=expires_in)

        return Response(
            {
                "token": token,
                "share_url": f"/share/{token}/",
                "expires_at": share_link.expires_at,
            },
            status=status.HTTP_201_CREATED
        )


class ShareLinkInfoView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(responses={200: {'properties': {'filename': {'type': 'string'}, 'expires_at': {'type': 'string'}, 'size': {'type': 'integer'}, 'expired': {'type': 'boolean'}}, 'type': 'object'}})
    def get(self, request, token):
        # Middleware already verified the token and extracted file_id
        file_id = getattr(request, 'verified_file_id', None)
        
        if file_id is None:
            # This shouldn't happen if middleware is configured correctly
            return Response({"detail": "Invalid or expired link."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            pdf_record = CompressedPDF.objects.get(id=file_id)
        except CompressedPDF.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(
            {
                "token": token,
                "filename": pdf_record.original_name,
                "size": pdf_record.original_size,
                "expired": False,  # If we got here, the token is valid (not expired)
            },
            status=status.HTTP_200_OK
        )


class SecureDownloadGatewayView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PublicLinkBurstThrottle]

    @extend_schema(exclude=True)
    def get(self, request, token):
        # Middleware already verified the token and extracted file_id
        file_id = getattr(request, 'verified_file_id', None)
        
        if file_id is None:
            # This shouldn't happen if middleware is configured correctly
            return render(request, "expired.html", {"error": "Invalid or expired link."}, status=403)
        
        try:
            pdf = CompressedPDF.objects.get(id=file_id)
        except CompressedPDF.DoesNotExist:
            return render(request, "expired.html", {"error": "File not found."}, status=404)

        # Determine which version of the file to serve (compressed or original)
        active_path = _resolve_active_path(pdf)
        
        # Generate a presigned download URL from Supabase (valid for 60 seconds)
        signed_url = make_presigned_download(active_path, expires_in=60)
        if not signed_url:
            return render(request, "expired.html", {"error": "Secure download link generation failed."}, status=500)

        # Redirect to presigned URL - browser downloads directly from Supabase
        return redirect(signed_url)
