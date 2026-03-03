from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import CustomUser


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Сериализатор для токенов"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "work_position",
            "password",
            "confirm_password",
        )

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = CustomUser.objects.create_user(**validated_data)
        return user


class CheckBuseEmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для проверки занятости сотрудников"""

    full_name = serializers.SerializerMethodField()
    active_tasks_count = serializers.IntegerField(read_only=True)
    active_tasks = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'work_position', 'full_name', 'active_tasks_count', 'active_tasks']

    def get_full_name(self, obj):
        return str(obj)

    def get_active_tasks(self, obj):
        return [str(task) for task in obj.active_tasks_list]
