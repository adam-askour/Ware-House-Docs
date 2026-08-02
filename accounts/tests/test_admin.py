import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from organization.models import ConfidentialAuthorization, Department, Membership

pytestmark = pytest.mark.django_db


def make_user(username, **kwargs):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="a-secure-password",
        **kwargs,
    )


def test_user_admin_displays_roles_and_explicit_confidential_grants(client):
    administrator = make_user("admin", is_staff=True, is_superuser=True)
    employee = make_user("employee", scanner_code="SCAN-001", is_reviewer=True)
    department = Department.objects.create(name="Legal", code="legal")
    Membership.objects.create(user=employee, department=department, role=Membership.Role.CHIEF)
    ConfidentialAuthorization.objects.create(
        user=employee,
        department=department,
        label="Legal confidential",
    )
    client.force_login(administrator)

    response = client.get(reverse("admin:accounts_user_change", args=(employee.pk,)))

    assert response.status_code == 200
    assert b"SCAN-001" in response.content
    content = response.content.lower()
    assert b"department memberships" in content
    assert b"explicit confidential authorizations" in content
    assert b"Legal confidential" in response.content


def test_creating_administrator_does_not_create_confidential_grant(client):
    administrator = make_user("admin", is_staff=True, is_superuser=True)
    client.force_login(administrator)

    response = client.post(
        reverse("admin:accounts_user_add"),
        {
            "username": "second-admin",
            "email": "second-admin@example.com",
            "password1": "another-secure-password",
            "password2": "another-secure-password",
            "membership_set-TOTAL_FORMS": "0",
            "membership_set-INITIAL_FORMS": "0",
            "membership_set-MIN_NUM_FORMS": "0",
            "membership_set-MAX_NUM_FORMS": "1000",
            "confidentialauthorization_set-TOTAL_FORMS": "0",
            "confidentialauthorization_set-INITIAL_FORMS": "0",
            "confidentialauthorization_set-MIN_NUM_FORMS": "0",
            "confidentialauthorization_set-MAX_NUM_FORMS": "1000",
        },
    )

    assert response.status_code == 302
    created = get_user_model().objects.get(username="second-admin")
    assert not ConfidentialAuthorization.objects.filter(user=created).exists()
