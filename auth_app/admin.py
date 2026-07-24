"""Django admin configuration for the custom email-based User model."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    """Admin panel configuration for the custom User model.

    Overrides Django's default UserAdmin field references, replacing
    `username` with `email` throughout, since this project's User model
    authenticates via email.
    """

    list_display = ("email", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser",
                        "groups", "user_permissions",)},),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "password1", "password2",
                           "is_staff", "is_active"), },),
    )


admin.site.register(User, UserAdmin)
