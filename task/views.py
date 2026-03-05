from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from task.models import Task
from task.paginators import CustomPagination
from task.permissions import IsTaskCreator, IsManager, IsTaskCreatorOrExecutor
from task.serializers import TaskSerializer
from task.services import get_important_tasks, get_employees_load, get_recommended_executor


class TaskViewSet(viewsets.ModelViewSet):
    """Представление ViewSet для работы с задачами"""
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at']
    ordering = ["-days_to_complete"]
    filterset_fields = ["executor", "task_manager", "status"]

    @swagger_auto_schema(
        operation_description="Создание",
        operation_summary="task_create",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Название задачи"
                ),
                "parent": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Наследуемая задача"
                ),
                "executor": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Исполнитель",
                ),
                "days_to_complete": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Кол-во дней для выполнения задания"
                ),
                "task_description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Описание задания",
                ),
            },
            required=["title", "task_description"],
        ),
        responses={
            "201": openapi.Response(
                description="Объект создан",
                schema=TaskSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "title": "Принятие товара",
                        "task_manager": 3,
                        "parent": None,
                        "executor": 5,
                        "date_to_complete": "03-03-2026 00:13",
                        "status": "started",
                        "task_description": "Поставщик доставил товар на склад. Необходимо оприходовать его.",
                        "created_at": "03-03-2026 00:13",
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "parent": [
                            "Недопустимый первичный ключ \"10\" - объект не существует.",
                        ]
                    }
                }
            ),
            "401": openapi.Response(
                description="Unauthorized",
                examples={
                    "application/json (Не авторизован)": {
                        "detail": "Учетные данные не были предоставлены."
                    },
                    "application/json (Недействительный токен)": {
                        "detail": "Данный токен недействителен для любого типа токена",
                        "code": "token_not_valid",
                        "messages": [
                            {
                                "token_class": "AccessToken",
                                "token_type": "access",
                                "message": "Token is expired"
                            }
                        ]
                    },
                },

            )
        },
        tags=["task"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """Фильтрует задачи для текущего пользователя - создатель или исполнитель"""
        user = self.request.user

        queryset = Task.objects.all()

        if self.action == 'list' and not user.groups.filter(name='manager').exists() and not user.is_superuser:
            return queryset.filter(
                Q(task_manager=user) | Q(executor=user)
            ).distinct()

        return queryset

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "update":
            self.permission_classes = [IsAuthenticated, IsTaskCreator | IsManager]
        elif self.action == "partial_update":
            self.permission_classes = [IsAuthenticated, IsTaskCreator | IsManager]
        elif self.action == "retrieve":
            self.permission_classes = [IsAuthenticated, IsTaskCreatorOrExecutor | IsManager]
        elif self.action == "create":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated, IsTaskCreator]
        if self.request.user.is_superuser:
            return []
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """Подготовка данных для сериализатора при создании объекта"""
        days = serializer.validated_data.get('days_to_complete', 2)
        parent = serializer.validated_data.get('parent')
        executor = serializer.validated_data.get('executor')

        date_to_complete = timezone.now() + timedelta(days=days)

        if parent and parent.date_to_complete:
            if date_to_complete > parent.date_to_complete:
                raise ValidationError({
                    'days_to_complete': (
                        f"Срок выполнения ({parent.related_task}) не может быть "
                        f"больше срока родительской задачи ({parent}) - "
                        f"{parent.date_to_complete.strftime("%d-%m-%Y %H:%M")}."
                    )
                })

        if executor:
            status = 'started'
        else:
            status = 'created'

        serializer.save(task_manager=self.request.user, date_to_complete=date_to_complete, status=status)

    def perform_update(self, serializer):
        """Подготовка данных для сериализатора при обновлении объекта"""
        instance = self.get_object()

        days = serializer.validated_data.pop('days_to_complete', 0)
        parent = serializer.validated_data.get('parent', instance.parent)
        status = instance.status
        executor = serializer.validated_data.get('executor')

        if days != 0:
            date_to_complete = timezone.now() + timedelta(days=days)
        else:
            date_to_complete = serializer.validated_data.get(
                'date_to_complete',
                instance.date_to_complete
            )

        if parent and parent.date_to_complete < date_to_complete:
            raise ValidationError({
                'days_to_complete': (
                    f"Срок выполнения ({instance}) превышает срок наследуемой задачи ({parent})"
                    f" - {parent.date_to_complete.strftime("%d-%m-%Y %H:%M")}."
                )
            })

        if status == 'created' and executor:
            status = 'started'

        if status == 'started' and not executor:
            status = 'created'

        serializer.save(task_manager=instance.task_manager, date_to_complete=date_to_complete, status=status)


class ImportantTaskView(APIView):
    """Представления для вывода важных задач"""
    permission_classes = [IsAuthenticated, IsManager | permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Важные задачи",
        operation_summary="important_task",
        responses={
            "200": openapi.Response(
                description="OK",
                schema=TaskSerializer,
                examples={
                    "application/json": {
                        "count": 1,
                        "ordering": "date_to_complete",
                        "results": [
                            {
                                "task": "Провести рефакторинг",
                                "date_to_complete": "21-02-2026 11:46",
                                "executors": [
                                    "Смирнов Сидор Иванович",
                                    "Петров Сидор Александрович",
                                    "Соколов Олег Сидорович"
                                ]
                            }
                        ]
                    }
                },
            ),
            "401": openapi.Response(
                description="Учетные данные не были предоставлены.",
                examples={
                    "application/json": {
                        "detail": "Учетные данные не были предоставлены."
                    }
                }
            ),
        },
        tags=["important_task"],
    )
    def get(self, request):
        statuses = ["started", "overdue"]
        ordering = request.query_params.get('ordering', 'date_to_complete')
        validate_ordering = ['date_to_complete', '-date_to_complete']

        if ordering not in validate_ordering:
            ordering = 'date_to_complete'
        # Получаем важные задачи
        tasks = get_important_tasks(ordering, statuses)
        # Получаем информацию о загруженности всех сотрудников
        employees_load = get_employees_load(statuses)
        # Отбираем первые 5 сотрудников у которых активных задач не более 2
        first_five_least_loaded = employees_load.filter(active_tasks_count__lte=2)[:4]

        result = []
        for task in tasks:
            # Получаем имя свободного сотрудника
            recommended_executor_name = get_recommended_executor(task, first_five_least_loaded, employees_load)
            result.append({
                'task': task.title,
                'date_to_complete': task.date_to_complete.strftime("%d-%m-%Y %H:%M"),
                'executors': recommended_executor_name
            })

        return Response({
            'count': len(result),
            'ordering': ordering,
            'results': result
        })
