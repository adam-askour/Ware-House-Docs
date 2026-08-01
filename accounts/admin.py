from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class DmsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Document management", {"fields": ("scanner_code", "is_reviewer")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Document management", {"fields": ("email", "scanner_code", "is_reviewer")}),
    )
    list_display = ("username", "email", "is_active", "is_reviewer", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "scanner_code")
