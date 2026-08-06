from django.db.models import Q

from organization.models import Membership


class AccessPolicy:
    """Deny-by-default authorization helpers shared by views and services."""

    @staticmethod
    def is_department_member(user, department) -> bool:
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(
                user=user, department=department, department__is_active=True, is_active=True
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
    def is_department_supervisor(user, department) -> bool:
        """Return whether the user has supervisor-or-higher authority."""
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(
                user=user,
                department=department,
                department__is_active=True,
                role__in=(Membership.Role.SUPERVISOR, Membership.Role.CHIEF),
                is_active=True,
            ).exists()
        )

    @staticmethod
    def has_confidential_authorization(user, department, label=None) -> bool:
        """Chief-only documents cannot be delegated below the department chief."""
        return AccessPolicy.is_department_chief(user, department)

    @staticmethod
    def visible_documents(user):
        from documents.models import Document

        if not user.is_authenticated or not user.is_active:
            return Document.objects.none()
        department_ids = Membership.objects.filter(
            user=user, is_active=True, department__is_active=True
        ).values_list("department_id", flat=True)
        supervisor_department_ids = Membership.objects.filter(
            user=user,
            role__in=(Membership.Role.SUPERVISOR, Membership.Role.CHIEF),
            is_active=True,
            department__is_active=True,
        ).values_list("department_id", flat=True)
        chief_department_ids = Membership.objects.filter(
            user=user,
            role=Membership.Role.CHIEF,
            is_active=True,
            department__is_active=True,
        ).values_list("department_id", flat=True)
        allowed = Q(
            sensitivity=Document.Sensitivity.NORMAL,
            assignments__department_id__in=department_ids,
        )
        supervisor = Q(
            sensitivity=Document.Sensitivity.SUPERVISOR,
            assignments__department_id__in=supervisor_department_ids,
        )
        chief_only = Q(
            sensitivity=Document.Sensitivity.CONFIDENTIAL,
            assignments__department_id__in=chief_department_ids,
        )
        return Document.objects.filter(allowed | supervisor | chief_only).distinct()

    @staticmethod
    def can_upload_to(user, department, sensitivity, label="") -> bool:
        from documents.models import Document

        if not AccessPolicy.is_department_member(user, department):
            return False
        if sensitivity == Document.Sensitivity.CONFIDENTIAL:
            return AccessPolicy.is_department_chief(user, department)
        if sensitivity == Document.Sensitivity.SUPERVISOR:
            return AccessPolicy.is_department_supervisor(user, department)
        return sensitivity == Document.Sensitivity.NORMAL
