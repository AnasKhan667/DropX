from rest_framework import permissions

class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated and 
            request.user.role in ['Driver', 'Both']
        )

class IsVerifiedDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated and 
            request.user.role in ['Driver', 'Both'] and 
            getattr(request.user, 'is_driver_verified', False)
        )

class IsSender(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated and 
            request.user.role in ['Sender', 'Both']
        )
