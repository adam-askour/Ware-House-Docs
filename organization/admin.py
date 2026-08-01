from django.contrib import admin

from .models import ConfidentialAuthorization, Department, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    inlines = (MembershipInline,)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "is_active")
    list_filter = ("role", "is_active", "department")
    search_fields = ("user__username", "user__email", "department__name")


@admin.register(ConfidentialAuthorization)
class ConfidentialAuthorizationAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "label", "is_active")
    list_filter = ("is_active", "department")
    search_fields = ("user__username", "user__email", "label")
