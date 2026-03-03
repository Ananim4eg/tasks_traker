from django.db.models import Count, Q, Prefetch
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from task.models import Task
from users.models import CustomUser
from users.serializers import UserRegistrationSerializer, CheckBuseEmployeeSerializer


class RegisterView(APIView):
    """Представление для регистрации"""

    @swagger_auto_schema(
        operation_description="Регистрация",
        operation_summary="Регистрация нового пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Почта"),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Пароль"
                ),
                "confirm_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Подтверждение пароля"
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Имя"
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Фамилия"
                ),
                "patronymic": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Отчество"
                ),
                "work_position": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Должность"
                ),
                "department": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Подразделение"
                ),
            },
            required=["email", "password", "confirm_password", "first_name", "last_name", "patronymic", "work_position"],
        ),
        responses={
            201: openapi.Response(description="Пользователь успешно зарегистрирован"),
            400: "Ошибка валидации данных",
        },
        tags=["register"],
    )

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response("Пользователь успешно зарегистрирован", status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckBusyEmployeeView(APIView):
    """Представление для вывода информации о загруженности сотрудников"""

    def get(self, request):
        statuses = ["started", "overdue"]
        ordering = request.query_params.get('ordering', '-active_tasks_count')
        validate_ordering = ['active_tasks_count', '-active_tasks_count']

        if ordering not in validate_ordering:
            ordering = '-active_tasks_count'

        employees =  CustomUser.objects.annotate(
            active_tasks_count=Count(
                'executor_task',
                filter=Q(executor_task__status__in=statuses)
            )
        ).prefetch_related(
            Prefetch(
                'executor_task',
                queryset=Task.objects.filter(status__in=statuses),
                to_attr='active_tasks_list'
            )
        ).order_by(ordering)

        serializer = CheckBuseEmployeeSerializer(employees, many=True)

        return Response({
            'ordering': ordering,
            'count': employees.count(),
            'results': serializer.data
        })
