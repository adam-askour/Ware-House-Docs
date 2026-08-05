from django.db.models import Q

from organization.models import ConfidentialAuthorization, Membership


class AccessPolicy:
    """Deny-by-default authorization helpers shared by views and services."""

    @staticmethod
    def is_department_member(user, department) -> bool:
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(
                user=user,
                department=department,
                department__is_active=True,
                is_active=True,
            ).exists()
        )

    @staticmethod
    def is_department_chief(user, department) -> bool:
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(
                user=user,
                department=department,
                department__is_active=True,
                role=Membership.Role.CHIEF,
                is_active=True,
            ).exists()
        )

    @staticmethod
    def has_confidential_authorization(user, department, label=None) -> bool:
        if not user.is_authenticated or not user.is_active:
            return False
        # An active department chief is responsible for the whole department,
        # so the role itself grants access to every confidential label there.
        if AccessPolicy.is_department_chief(user, department):
            return True
        grants = ConfidentialAuthorization.objects.filter(
            user=user,
            department=department,
            department__is_active=True,
            is_active=True,
        )
        if label is not None:
            # Labels are currently administrator-entered free text. Treat casing as
            # presentation, while keeping the actual wording an exact match.
            grants = grants.filter(label__iexact=label)
        return grants.exists()

    @staticmethod
    def visible_documents(user):
        from documents.models import Document

        if not user.is_authenticated or not user.is_active:
            return Document.objects.none()
        department_ids = Membership.objects.filter(
            user=user, is_active=True, department__is_active=True
        ).values_list("department_id", flat=True)
        allowed = Q(
            sensitivity=Document.Sensitivity.NORMAL,
            assignments__department_id__in=department_ids,
        )
        chief_department_ids = Membership.objects.filter(
            user=user,
            role=Membership.Role.CHIEF,
            is_active=True,
            department__is_active=True,
        ).values_list("department_id", flat=True)
        confidential = Q(
            sensitivity=Document.Sensitivity.CONFIDENTIAL,
            assignments__department_id__in=chief_department_ids,
        )
        grants = ConfidentialAuthorization.objects.filter(
            user=user, is_active=True, department__is_active=True
        ).values_list("department_id", "label")
        for department_id, label in grants:
            confidential |= Q(
                sensitivity=Document.Sensitivity.CONFIDENTIAL,
                confidential_label__iexact=label,
                assignments__department_id=department_id,
            )
        return Document.objects.filter(allowed | confidential).distinct()

    @staticmethod
    def can_upload_to(user, department, sensitivity, label="") -> bool:
        from documents.models import Document

        if not AccessPolicy.is_department_member(user, department):
            return False
        if sensitivity == Document.Sensitivity.CONFIDENTIAL:
            return AccessPolicy.has_confidential_authorization(user, department, label)
        return sensitivity == Document.Sensitivity.NORMAL
