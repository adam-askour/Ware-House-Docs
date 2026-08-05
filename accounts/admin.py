from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from organization.models import ConfidentialAuthorization, Membership

from .models import User


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    verbose_name = "department membership"
    verbose_name_plural = "department memberships"


class ConfidentialAuthorizationInline(admin.TabularInline):
    model = ConfidentialAuthorization
    extra = 0
    verbose_name = "explicit confidential authorization"
    verbose_name_plural = "explicit confidential authorizations"


@admin.register(User)
class DmsUserAdmin(UserAdmin):
    # Staff/group/permission flags are intentionally absent: administrator
    # access is reserved for superusers created through the management command.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Account status", {"fields": ("is_active",)}),
        ("Document management", {"fields": ("scanner_code",)}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Document management", {"fields": ("email", "scanner_code")}),
    )
    list_display = ("username", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("username", "email", "first_name", "last_name", "scanner_code")
    inlines = (MembershipInline, ConfidentialAuthorizationInline)
