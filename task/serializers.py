from rest_framework import serializers

from task.models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "task_manager",
            "parent",
            "executor",
            "time_to_complete",
            "status",
            "task_description",
            "created_at",
        ]
