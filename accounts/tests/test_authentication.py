import pytest
from django.contrib.auth import authenticate, get_user_model

pytestmark = pytest.mark.django_db


def test_password_is_hashed():
    user = get_user_model().objects.create_user(
        username="sam", email="sam@example.com", password="a-secure-password"
    )
    assert user.password != "a-secure-password"
    assert user.check_password("a-secure-password")


def test_user_can_authenticate_with_username_or_email():
    get_user_model().objects.create_user(
        username="sam", email="sam@example.com", password="a-secure-password"
    )
    assert authenticate(username="sam", password="a-secure-password") is not None
    assert authenticate(username="SAM@EXAMPLE.COM", password="a-secure-password") is not None


def test_deactivated_user_cannot_authenticate():
    get_user_model().objects.create_user(
        username="sam", email="sam@example.com", password="a-secure-password", is_active=False
    )
    assert authenticate(username="sam", password="a-secure-password") is None
