from rest_framework import serializers

from task.models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""
    days_to_complete = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    created_at = serializers.DateTimeField(
        format="%d-%m-%Y %H:%M",
        read_only=True
    )
    date_to_complete = serializers.DateTimeField(
        format="%d-%m-%Y %H:%M",
        read_only=True
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "task_manager",
            "parent",
            "executor",
            "days_to_complete",
            "date_to_complete",
            "status",
            "task_description",
            "created_at",
        ]

    def validate(self, data):
        user = self.context['request'].user

        if user.is_superuser:
            return data

        if user.has_perm('task.change_task'):
            return data

        if user.groups.filter(name='manager').exists():
            if self.instance:
                for field, value in data.items():
                    old_value = getattr(self.instance, field)

                    allowed_fields = ['title', 'executor', 'task_description', 'days_to_complete', 'date_to_complete']

                    if field not in allowed_fields and value != old_value:
                        raise serializers.ValidationError(
                            f"У вас нет прав на изменение поля '{field}'"
                        )
        return data

    def to_representation(self, instance):
        """Преобразуем поля в читаемый вид"""
        representation = super().to_representation(instance)

        if instance.task_manager:
            representation['task_manager'] = str(instance.task_manager)
        else:
            representation['task_manager'] = None

        if instance.executor:
            representation['executor'] = str(instance.executor)
        else:
            representation['executor'] = None

        if instance.parent:
            representation['parent'] = str(instance.parent)
        else:
            representation['parent'] = None

        if instance.status:
            representation['status'] = instance.get_status_display()
        else:
            representation['status'] = None

        return representation
