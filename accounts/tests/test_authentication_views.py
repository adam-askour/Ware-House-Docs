import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db


def make_user(username="sam", **kwargs):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="a-secure-password",
        **kwargs,
    )


def test_login_page_renders(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"Sign in" in response.content


def test_user_can_log_in_with_email_through_login_page(client):
    user = make_user()
    response = client.post(
        reverse("login"),
        {"username": user.email.upper(), "password": "a-secure-password"},
    )

    assert response.status_code == 302
    assert response.url == reverse("core:home")
    assert client.session["_auth_user_id"] == str(user.pk)


def test_employee_landing_page_requires_login_and_accepts_non_staff_user(client):
    anonymous_response = client.get(reverse("core:home"))
    assert anonymous_response.status_code == 302
    assert anonymous_response.url.startswith(reverse("login"))

    client.force_login(make_user())
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert b"Welcome" in response.content
    assert b"Administration" not in response.content


def test_password_change_pages_render_for_authenticated_user(client):
    client.force_login(make_user())

    form_response = client.get(reverse("password_change"))
    done_response = client.get(reverse("password_change_done"))

    assert form_response.status_code == 200
    assert b"Change password" in form_response.content
    assert done_response.status_code == 200
    assert b"Password changed" in done_response.content


def test_deactivated_user_cannot_log_in_through_login_page(client):
    make_user(is_active=False)
    response = client.post(
        reverse("login"),
        {"username": "sam", "password": "a-secure-password"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
