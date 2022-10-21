from rest_framework import permissions


class IsAdminAuthorOrReadOnly(permissions.BasePermission):
    """
    Проверка наличия прав. Анонимный пользователь
    может только всё просматривать.
    Изменять контент может только администратор или автор.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if (request.user.is_admin
               or obj.author == request.user):
                return True
        return request.method in permissions.SAFE_METHODS
