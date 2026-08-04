from django import forms

from access.policies import AccessPolicy
from organization.models import Department

from .models import Document
from .services import validate_pdf


class ManualUploadForm(forms.Form):
    title = forms.CharField(max_length=255)
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    sensitivity = forms.ChoiceField(choices=Document.Sensitivity.choices)
    confidential_label = forms.ChoiceField(choices=(), required=False)
    file = forms.FileField(help_text="PDF files only. Encrypted PDFs are not accepted.")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["department"].queryset = Department.objects.filter(
            membership__user=user,
            membership__is_active=True,
            is_active=True,
        ).distinct()
        labels = (
            user.confidentialauthorization_set.filter(
                is_active=True, department__is_active=True
            )
            .order_by("label")
            .values_list("label", flat=True)
            .distinct()
        )
        self.fields["confidential_label"].choices = [("", "---------")] + [
            (label, label) for label in labels
        ]

    def clean_file(self):
        upload = self.cleaned_data["file"]
        validate_pdf(upload)
        return upload

    def clean(self):
        cleaned = super().clean()
        department = cleaned.get("department")
        sensitivity = cleaned.get("sensitivity")
        label = cleaned.get("confidential_label", "").strip()
        if sensitivity == Document.Sensitivity.CONFIDENTIAL and not label:
            self.add_error("confidential_label", "A confidential label is required.")
        if sensitivity == Document.Sensitivity.NORMAL and label:
            self.add_error("confidential_label", "Normal documents cannot have a label.")
        if department and sensitivity and not AccessPolicy.can_upload_to(
            self.user, department, sensitivity, label
        ):
            raise forms.ValidationError("You are not authorized for this upload destination.")
        cleaned["confidential_label"] = label
        return cleaned
