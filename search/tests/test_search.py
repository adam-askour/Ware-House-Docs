import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from documents.models import (
    Document,
    DocumentDepartment,
    DocumentMetadata,
    DocumentVersion,
    StoredFile,
)
from ocr.models import OcrJob, OcrPageText
from organization.models import Department, Membership
from search.services import rebuild_document_search, search_pages

pytestmark = pytest.mark.django_db


def make_user(name):
    return get_user_model().objects.create_user(
        username=name, email=f"{name}@example.com", password="a-secure-password"
    )


def make_document(user, department, *, title, pages, sensitivity=Document.Sensitivity.NORMAL):
    document = Document.objects.create(
        title=title,
        status=Document.Status.PUBLISHED,
        sensitivity=sensitivity,
        confidential_label="restricted" if sensitivity == Document.Sensitivity.CONFIDENTIAL else "",
        created_by=user,
    )
    DocumentDepartment.objects.create(document=document, department=department, is_primary=True)
    stored = StoredFile.objects.create(
        file=f"test/{document.pk}.pdf", sha256=f"{document.pk:064x}", size=1
    )
    version = DocumentVersion.objects.create(
        document=document,
        number=1,
        stored_file=stored,
        original_filename="sample.pdf",
        created_by=user,
    )
    job = OcrJob.objects.create(version=version, status=OcrJob.Status.SUCCEEDED)
    for number, text in enumerate(pages, 1):
        OcrPageText.objects.create(job=job, page_number=number, text=text)
    rebuild_document_search(document)
    return document


def test_title_match_outranks_body_only_match():
    user = make_user("employee")
    department = Department.objects.create(name="Accounting", code="accounting")
    Membership.objects.create(user=user, department=department)
    title_match = make_document(user, department, title="Quarterly invoice", pages=["Other text"])
    body_match = make_document(user, department, title="Quarterly report", pages=["Invoice details"])

    results = list(search_pages(user=user, query_text="invoice"))

    assert [result.document for result in results] == [title_match, body_match]
    assert results[0].rank > results[1].rank


def test_body_match_returns_page_and_viewer_deep_link(client):
    user = make_user("reader")
    department = Department.objects.create(name="Operations", code="operations")
    Membership.objects.create(user=user, department=department)
    document = make_document(
        user, department, title="Manual", pages=["Introduction", "Emergency shutdown procedure"]
    )
    client.force_login(user)

    response = client.get(reverse("search:results"), {"q": "shutdown"})

    assert response.status_code == 200
    assert response.context["results"][0].page_number == 2
    assert f'{reverse("documents:viewer", args=(document.pk,))}?page=2' in response.content.decode()


def test_unauthorized_document_does_not_appear_or_affect_count(client):
    user = make_user("limited")
    owner = make_user("owner")
    visible_department = Department.objects.create(name="Visible", code="visible")
    hidden_department = Department.objects.create(name="Hidden", code="hidden")
    Membership.objects.create(user=user, department=visible_department)
    Membership.objects.create(user=owner, department=hidden_department)
    visible = make_document(owner, visible_department, title="Visible", pages=["needle"])
    hidden = make_document(owner, hidden_department, title="Secret title", pages=["needle"])
    client.force_login(user)

    response = client.get(reverse("search:results"), {"q": "needle"})

    assert [result.document for result in response.context["results"]] == [visible]
    content = response.content.decode()
    assert "1 accessible document found" in content
    assert hidden.title not in content


@pytest.mark.parametrize("token", ["facture", "العربية", "contract"])
def test_french_arabic_and_english_exact_tokens_are_searchable(token):
    user = make_user(f"reader-{len(token)}")
    department = Department.objects.create(name=token, code=f"d-{len(token)}")
    Membership.objects.create(user=user, department=department)
    document = make_document(
        user,
        department,
        title="Multilingual sample",
        pages=["facture française خطاب العربية printed contract"],
    )

    assert list(search_pages(user=user, query_text=token))[0].document == document


def test_metadata_and_document_filters_combine():
    user = make_user("filter-user")
    first = Department.objects.create(name="First", code="first")
    second = Department.objects.create(name="Second", code="second")
    Membership.objects.create(user=user, department=first)
    Membership.objects.create(user=user, department=second)
    wanted = make_document(user, first, title="Record", pages=["ordinary body"])
    DocumentMetadata.objects.create(document=wanted, key="reference", value="PO-441")
    rebuild_document_search(wanted)
    make_document(user, second, title="Record", pages=["PO-441"])

    results = list(
        search_pages(
            user=user,
            query_text="PO-441",
            department="first",
            status=Document.Status.PUBLISHED,
            sensitivity=Document.Sensitivity.NORMAL,
        )
    )

    assert [result.document for result in results] == [wanted]
