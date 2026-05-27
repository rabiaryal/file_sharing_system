from rest_framework import serializers
from .models import CompressedPDF, ShareLink

class UploadIntentSerializer(serializers.Serializer):
    filename = serializers.CharField()
    size = serializers.IntegerField()

class ProcessSerializer(serializers.Serializer):
    storage_path = serializers.CharField()
    original_name = serializers.CharField()
    original_size = serializers.IntegerField()
    expires_in_seconds = serializers.IntegerField(default=86400, min_value=3600, max_value=86400*30)

class ShareLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareLink
        fields = ["expires_at", "created_at"]
