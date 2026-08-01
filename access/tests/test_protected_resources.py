import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def make_user(username, **kwargs):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="a-secure-password",
        **kwargs,
    )


@override_settings(DEBUG=False)
def test_protected_file_cannot_be_retrieved_through_guessed_direct_urls(client, tmp_path):
    marker = b"PRIVATE-DOCUMENT-CONTENT"
    protected_root = tmp_path / "protected"
    protected_root.mkdir()
    (protected_root / "private.pdf").write_bytes(marker)

    with override_settings(MEDIA_ROOT=protected_root):
        for url in ("/media/private.pdf", "/protected/private.pdf"):
            response = client.get(url)

            assert response.status_code == 404
            assert marker not in response.content


def test_anonymous_direct_admin_object_url_returns_no_protected_content(client):
    protected_user = make_user("private-record")
    url = reverse("admin:accounts_user_change", args=(protected_user.pk,))

    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))
    assert protected_user.email.encode() not in response.content


def test_authenticated_non_staff_user_cannot_open_direct_admin_object_url(client):
    requester = make_user("employee")
    protected_user = make_user("private-record")
    client.force_login(requester)

    response = client.get(reverse("admin:accounts_user_change", args=(protected_user.pk,)))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))
    assert protected_user.email.encode() not in response.content


def test_staff_user_without_model_permission_cannot_open_direct_admin_object_url(client):
    requester = make_user("staff", is_staff=True)
    protected_user = make_user("private-record")
    client.force_login(requester)

    response = client.get(reverse("admin:accounts_user_change", args=(protected_user.pk,)))

    assert response.status_code == 403
    assert protected_user.email.encode() not in response.content
