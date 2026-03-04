from django.db import models

from users.models import CustomUser


class Task(models.Model):
    """Модель задач"""

    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('started', 'Запущена'),
        ('overdue', 'Просрочена'),
        ('stoped', 'Завершена'),
    ]

    title = models.CharField(
        max_length=50,
        verbose_name="Название задачи"
    )
    task_manager = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="task_manager",
        verbose_name="Постановщик задачи",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='related_task',
        verbose_name="Наследуемая задача"
    )
    executor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="executor_task",
        verbose_name="Исполнитель"
    )
    days_to_complete = models.SmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Кол-во дней для выполнения задания"
    )
    date_to_complete = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата, до которой должна быть выполнена задача"
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        default='created',
        verbose_name="Статус задачи"
    )
    task_description = models.TextField(
        max_length=1500,
        verbose_name="Описание задания"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-created_at"]
