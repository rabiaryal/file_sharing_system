from django.urls import path, register_converter

from core.converters import TokenConverter
from .views import ProcessView, SecureDownloadGatewayView, UploadIntentView, ShareLinkInfoView

register_converter(TokenConverter, 'token')

urlpatterns = [
    path("upload-intent/", UploadIntentView.as_view(), name="upload-intent"),
    path("process/", ProcessView.as_view(), name="process"),
    # Token format: <file_id>:<expiry>:<signature> (stateless HMAC tokens)
    path("share/<token:token>/info/", ShareLinkInfoView.as_view(), name="share-link-info"),
    path("share/<token:token>/", SecureDownloadGatewayView.as_view(), name="secure-download-gateway"),
]
