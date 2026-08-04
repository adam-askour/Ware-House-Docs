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
