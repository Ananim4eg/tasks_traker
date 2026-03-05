from rest_framework.permissions import BasePermission


class IsTaskCreatorOrExecutor(BasePermission):
    """Разрешает доступ только к своим объектам"""

    def has_object_permission(self, request, view, obj):
        return obj.task_manager == request.user or obj.executor == request.user


class IsTaskCreator(BasePermission):
    """Разрешает доступ только создателю задачи"""

    def has_object_permission(self, request, view, obj):
        return obj.task_manager == request.user


class IsOwner(BasePermission):
    """Разрешает доступ к личному профилю"""

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsManager(BasePermission):
    """Проверка, что пользователь добавлен в группу менеджер, который может редактировать определенные поля объектов"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='manager').exists()
