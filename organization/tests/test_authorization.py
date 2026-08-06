import pytest
from django.contrib.auth import get_user_model

from access.policies import AccessPolicy
from organization.models import ConfidentialAuthorization, Department, Membership

pytestmark = pytest.mark.django_db


def make_user(username, **kwargs):
    return get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="a-secure-password", **kwargs
    )


def test_user_can_belong_to_several_departments():
    user = make_user("sam")
    first = Department.objects.create(name="Legal", code="legal")
    second = Department.objects.create(name="Finance", code="finance")
    Membership.objects.create(user=user, department=first)
    Membership.objects.create(user=user, department=second)
    assert set(user.department_set.all()) == {first, second}


def test_ordinary_member_cannot_perform_chief_actions():
    user = make_user("sam")
    department = Department.objects.create(name="Legal", code="legal")
    Membership.objects.create(user=user, department=department)
    assert AccessPolicy.is_department_member(user, department)
    assert not AccessPolicy.is_department_chief(user, department)


def test_chief_authority_is_scoped_to_the_department():
    user = make_user("sam")
    legal = Department.objects.create(name="Legal", code="legal")
    finance = Department.objects.create(name="Finance", code="finance")
    Membership.objects.create(user=user, department=legal, role=Membership.Role.CHIEF)
    Membership.objects.create(user=user, department=finance)
    assert AccessPolicy.is_department_chief(user, legal)
    assert not AccessPolicy.is_department_chief(user, finance)


def test_administrator_does_not_automatically_receive_confidential_access():
    admin = make_user("admin", is_staff=True, is_superuser=True)
    department = Department.objects.create(name="Legal", code="legal")
    assert not AccessPolicy.has_confidential_authorization(admin, department)
    ConfidentialAuthorization.objects.create(user=admin, department=department, label="Legal confidential")
    assert not AccessPolicy.has_confidential_authorization(admin, department, "Legal confidential")


def test_chief_receives_confidential_access_without_staff_or_explicit_grant():
    chief = make_user("chief")
    department = Department.objects.create(name="Compliance", code="compliance")
    Membership.objects.create(user=chief, department=department, role=Membership.Role.CHIEF)

    assert not chief.is_staff
    assert AccessPolicy.has_confidential_authorization(chief, department, "Any label")


def test_explicit_grant_does_not_override_chief_only_visibility():
    user = make_user("sam")
    department = Department.objects.create(name="Payroll", code="payroll")
    ConfidentialAuthorization.objects.create(
        user=user, department=department, label="Payroll confidential"
    )

    assert not AccessPolicy.has_confidential_authorization(
        user, department, "payroll confidential"
    )


def test_supervisor_authority_is_between_employee_and_chief():
    user = make_user("supervisor")
    department = Department.objects.create(name="Operations", code="operations")
    Membership.objects.create(
        user=user, department=department, role=Membership.Role.SUPERVISOR
    )

    assert AccessPolicy.is_department_member(user, department)
    assert AccessPolicy.is_department_supervisor(user, department)
    assert not AccessPolicy.is_department_chief(user, department)


def test_inactive_membership_and_user_are_denied():
    user = make_user("sam")
    department = Department.objects.create(name="Legal", code="legal")
    Membership.objects.create(user=user, department=department, role=Membership.Role.CHIEF, is_active=False)
    assert not AccessPolicy.is_department_member(user, department)
    assert not AccessPolicy.is_department_chief(user, department)


def test_inactive_department_denies_all_department_scoped_access():
    user = make_user("sam")
    department = Department.objects.create(name="Legal", code="legal", is_active=False)
    Membership.objects.create(user=user, department=department, role=Membership.Role.CHIEF)
    ConfidentialAuthorization.objects.create(
        user=user, department=department, label="Legal confidential"
    )

    assert not AccessPolicy.is_department_member(user, department)
    assert not AccessPolicy.is_department_chief(user, department)
    assert not AccessPolicy.has_confidential_authorization(
        user, department, "Legal confidential"
    )
