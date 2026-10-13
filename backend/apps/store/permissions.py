from rest_framework.permissions import BasePermission, SAFE_METHODS
def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or (hasattr(user, "profile") and user.profile.role == "admin")))
class IsStoreAdmin(BasePermission):
    def has_permission(self, request, view): return is_admin(request.user)
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_admin(request.user) or getattr(obj, "user_id", None) == request.user.id
class ProductWriteAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request.user)
