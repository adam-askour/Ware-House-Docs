from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.SlugField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Membership")

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Employee"
        SUPERVISOR = "supervisor", "Supervisor"
        CHIEF = "chief", "Department chief"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "department"), name="unique_department_membership")
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.department} ({self.get_role_display()})"


class ConfidentialAuthorization(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "department", "label"), name="unique_confidential_authorization"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.department}: {self.label}"
