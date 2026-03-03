from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import is_only_letters


class CustomUserManager(BaseUserManager):
    """Управление созданием пользователей"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Модель пользователей"""

    username = None
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    first_name = models.CharField(max_length=50, validators=[is_only_letters], verbose_name="Имя")
    last_name = models.CharField(max_length=50, validators=[is_only_letters], verbose_name="Фамилия")
    patronymic = models.CharField(max_length=50, validators=[is_only_letters], verbose_name="Отчество")
    work_position = models.CharField(max_length=100, verbose_name="Должность")
    department = models.CharField(max_length=100, verbose_name="Отдел", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["work_position", "first_name", "last_name", "patronymic",]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]
