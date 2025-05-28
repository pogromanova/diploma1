from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        safe_request = request.method in permissions.SAFE_METHODS
        user_auth = request.user.is_authenticated
        return safe_request or user_auth

    def has_object_permission(self, request, view, obj):
        safe_methods = permissions.SAFE_METHODS
        if request.method in safe_methods:
            return True
        
        is_author = obj.author == request.user
        return is_author