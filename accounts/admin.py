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
    fieldsets = UserAdmin.fieldsets + (("Document management", {"fields": ("scanner_code", "is_reviewer")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Document management", {"fields": ("email", "scanner_code", "is_reviewer")}),
    )
    list_display = ("username", "email", "is_active", "is_reviewer", "is_staff")
    list_filter = ("is_active", "is_reviewer", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name", "scanner_code")
    inlines = (MembershipInline, ConfidentialAuthorizationInline)
