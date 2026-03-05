from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from task.permissions import IsOwner, IsManager
from task.services import get_employees_load
from users.models import CustomUser
from users.serializers import UserRegistrationSerializer, CheckBuseEmployeeSerializer, UserSerializer


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
            required=[
                "email",
                "password",
                "confirm_password",
                "first_name",
                "last_name",
                "patronymic",
                "work_position"
            ],
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
    permission_classes = [IsAuthenticated, IsManager | permissions.IsAdminUser]

    def get(self, request):
        statuses = ["started", "overdue"]
        ordering = request.query_params.get('ordering', '-active_tasks_count')
        validate_ordering = ['active_tasks_count', '-active_tasks_count']

        if ordering not in validate_ordering:
            ordering = '-active_tasks_count'
        # Получаем информацию о загруженности всех сотрудников
        employees = get_employees_load(statuses, ordering)
        # Отправляем данные в серилизатор
        serializer = CheckBuseEmployeeSerializer(employees, many=True)

        return Response({
            'ordering': ordering,
            'count': employees.count(),
            'results': serializer.data
        })


class UserListView(ListAPIView):
    """Представление для просмотра списка пользователей"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManager | permissions.IsAdminUser]


class UserDetailView(RetrieveAPIView):
    """Представление для просмотра отдельного пользователя"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwner | IsManager | permissions.IsAdminUser]


class UserUpdateView(UpdateAPIView):
    """Представление для обновления пользователя"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwner | IsManager | permissions.IsAdminUser]


class UserDeleteView(DestroyAPIView):
    """Представление для удаления пользователя"""
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
