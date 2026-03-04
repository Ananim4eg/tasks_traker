from django.core.management.base import BaseCommand
from django.db import transaction

from task.models import Task
from users.models import CustomUser


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-superuser',
            action='store_true',
            default=False,
            help='Удалить суперпользователя'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Начинаем сброс данных...'))

        delete_superuser = options['delete_superuser']

        # Удаляем задачи
        task_count = Task.objects.count()
        Task.objects.all().delete()
        self.stdout.write(f'Удалено {task_count} задач')

        # Удаляем пользователей
        if delete_superuser:
            # Удаляем всех
            user_count = CustomUser.objects.count()
            CustomUser.objects.all().delete()
            self.stdout.write(f'Удалено {user_count} всех пользователей')
        else:
            # Удаляем всех, кроме суперпользователей
            user_count = CustomUser.objects.filter(is_superuser=False).count()
            CustomUser.objects.filter(is_superuser=False).delete()
            self.stdout.write(f'Удалено {user_count} обычных пользователей')
            self.stdout.write('Оставлен суперпользователь')

        self.stdout.write(self.style.SUCCESS('Сброс данных завершен'))
