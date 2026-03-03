from datetime import timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from task.models import Task
from task.paginators import CustomPagination
from task.serializers import TaskSerializer


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
                    type=openapi.TYPE_INTEGER,description="Исполнитель",
                ),
                "days_to_complete": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Кол-во дней для выполнения задания"
                ),
                "task_description": openapi.Schema(
                    type=openapi.TYPE_STRING,description="Описание задания",
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
                        "status": "created",
                        "task_description": "Поставщик доставил товар на склад. Необходимо оприходовать его в системе.",
                        "created_at": "03-03-2026 00:13",
                    }
                },
            ),
            "400": "Ошибки валидации",
            "401": "Не авторизован",
        },
        tags=["task"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "update":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "partial_update":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "retrieve":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "create":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]


    def perform_create(self, serializer):
        """Подготовка данных для сериализатора при создании объекта"""
        days = serializer.validated_data.get('days_to_complete', 2)

        date_to_complete = timezone.now() + timedelta(days=days)

        serializer.save(task_manager=self.request.user,date_to_complete=date_to_complete)

    def perform_update(self, serializer):
        """Подготовка данных для сериализатора при обновлении объекта"""
        days = serializer.validated_data.pop('days_to_complete', 0)
        status = self.get_object().status
        executor = serializer.validated_data.get('executor')

        if days != 0:
            date_to_complete = timezone.now() + timedelta(days=days)
        else:
            date_to_complete = serializer.validated_data.get('date_to_complete')

        if status == 'created' and executor:
            status = 'started'

        serializer.save(task_manager=self.request.user,date_to_complete=date_to_complete, status=status)
