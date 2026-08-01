from organization.models import ConfidentialAuthorization, Membership


class AccessPolicy:
    """Deny-by-default authorization helpers shared by views and services."""

    @staticmethod
    def is_department_member(user, department) -> bool:
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(user=user, department=department, is_active=True).exists()
        )

    @staticmethod
    def is_department_chief(user, department) -> bool:
        return bool(
            user.is_authenticated
            and user.is_active
            and Membership.objects.filter(
                user=user, department=department, role=Membership.Role.CHIEF, is_active=True
            ).exists()
        )

    @staticmethod
    def has_confidential_authorization(user, department, label=None) -> bool:
        if not user.is_authenticated or not user.is_active:
            return False
        grants = ConfidentialAuthorization.objects.filter(user=user, department=department, is_active=True)
        if label is not None:
            grants = grants.filter(label=label)
        return grants.exists()
