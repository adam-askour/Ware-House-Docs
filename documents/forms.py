from django import forms

from access.policies import AccessPolicy
from organization.models import Department

from .models import Document
from .services import validate_pdf


class ManualUploadForm(forms.Form):
    title = forms.CharField(max_length=255)
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    sensitivity = forms.ChoiceField(choices=Document.Sensitivity.choices)
    confidential_label = forms.CharField(max_length=100, required=False, label="Chief-only label")
    file = forms.FileField(help_text="PDF files only. Encrypted PDFs are not accepted.")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        departments = Department.objects.filter(
            membership__user=user,
            membership__is_active=True,
            is_active=True,
        ).distinct()
        self.fields["department"].queryset = departments
        self.fields["sensitivity"].choices = [(Document.Sensitivity.NORMAL, "Normal")]
        roles = set(
            user.membership_set.filter(
                department__in=departments, is_active=True
            ).values_list("role", flat=True)
        )
        if roles & {"supervisor", "chief"}:
            self.fields["sensitivity"].choices.append(
                (Document.Sensitivity.SUPERVISOR, "Supervisor")
            )
        if "chief" in roles:
            self.fields["sensitivity"].choices.append(
                (Document.Sensitivity.CONFIDENTIAL, "Chief only")
            )

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
            self.add_error("confidential_label", "A chief-only label is required.")
        if sensitivity != Document.Sensitivity.CONFIDENTIAL and label:
            self.add_error(
                "confidential_label", "Only chief-only documents can have a label."
            )
        if department and sensitivity and not AccessPolicy.can_upload_to(
            self.user, department, sensitivity, label
        ):
            raise forms.ValidationError("You are not authorized for this upload destination.")
        cleaned["confidential_label"] = label
        return cleaned
