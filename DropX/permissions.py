from rest_framework.permissions import BasePermission


class IsDriver(BasePermission):
    """
    Allows access only to users with role Driver or Both.
    """
    def has_permission(self, request, view):
        return (
            getattr(request.user, 'is_authenticated', False)
            and request.user.role in ['Driver', 'Both']
        )


class IsVerifiedDriver(BasePermission):
    """
    Allows access only to verified drivers.
    Checks either:
    - request.user.is_driver_verified (boolean field on user), OR
    - request.user.driver_profile.is_driver_verified if using a related profile model.
    """
    def has_permission(self, request, view):
        if not getattr(request.user, 'is_authenticated', False):
            return False

        if request.user.role not in ['Driver', 'Both']:
            return False

        # Prefer direct field if available
        if hasattr(request.user, 'is_driver_verified'):
            return request.user.is_driver_verified

        # Fallback to driver_profile relation
        driver_profile = getattr(request.user, 'driver_profile', None)
        return getattr(driver_profile, 'is_driver_verified', False)


class IsSender(BasePermission):
    """
    Allows access only to users with role Sender or Both.
    """
    def has_permission(self, request, view):
        return (
            getattr(request.user, 'is_authenticated', False)
            and request.user.role in ['Sender', 'Both']
        )
