from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "phone", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_email_verified")
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "profile_picture")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_email_verified", "is_superuser", "groups", "user_permissions")} ),
        ("Timestamps", {"fields": ("created_at", "updated_at")} ),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password")} ),
    )
    search_fields = ("email", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")