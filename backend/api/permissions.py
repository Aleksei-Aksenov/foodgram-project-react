from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Проверка наличия прав. Анонимный пользователь
    может только всё просматривать.
    Изменять контент может только администратор или автор.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
