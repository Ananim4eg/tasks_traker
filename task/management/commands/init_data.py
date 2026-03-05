from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import random

from task.models import Task
from users.models import CustomUser


class Command(BaseCommand):
    """
    Кастомная команда для инициализации данных:
    - Создание группы менеджеров с правами
    - Создание тестовых пользователей
    - Создание тестовых задач
    """

    help = 'Инициализирует группу менеджеров, тестовых пользователей и задачи'

    def add_arguments(self, parser):
        """Добавляем аргументы командной строки"""
        parser.add_argument(
            '--users-count',
            type=int,
            default=10,
            help='Количество тестовых пользователей для создания (по умолчанию: 5)'
        )
        parser.add_argument(
            '--tasks-count',
            type=int,
            default=15,
            help='Количество тестовых задач для создания (по умолчанию: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Основная логика команды"""

        users_count = options['users_count']
        tasks_count = options['tasks_count']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('Начинаем инициализацию данных...'))

        # Очистка данных если нужно
        if clear_data:
            self.clear_existing_data()

        # Создание группы менеджеров
        manager_group = self.create_manager_group()

        # Создание суперпользователя
        superuser = self.create_superuser()

        # Создание пользователей
        users = self.create_test_users(users_count, manager_group)

        # Создание задач
        tasks = self.create_test_tasks(tasks_count, users, superuser)

        # Вывод статистики
        self.print_statistics(manager_group, users, tasks)

    def clear_existing_data(self):
        """Очистка существующих данных"""
        self.stdout.write('Очистка существующих данных...')

        # Удаляем все задачи
        Task.objects.all().delete()
        self.stdout.write('Задачи удалены')

        # Удаляем всех пользователей (кроме текущего суперпользователя, если есть)
        CustomUser.objects.exclude(is_superuser=True).delete()
        self.stdout.write('Пользователи удалены')

        # Удаляем группу менеджеров
        Group.objects.filter(name='manager').delete()
        self.stdout.write('Группы удалены')

    def create_manager_group(self):
        """Создание группы менеджеров с правами"""
        self.stdout.write('\nСоздание группы менеджеров...')

        # Создаем группу
        manager_group, created = Group.objects.get_or_create(name='manager')

        if created:
            self.stdout.write('Группа "manager" создана')
        else:
            self.stdout.write('Группа "manager" уже существует')

        # Получаем content type для модели Task
        task_content_type = ContentType.objects.get_for_model(Task)

        # Получаем кастомные permissions для задачи
        task_permissions = Permission.objects.filter(
            content_type=task_content_type,
            codename__in=[
                'view_task'
            ]
        )

        # Получаем content type для модели CustomUser
        user_content_type = ContentType.objects.get_for_model(CustomUser)

        # Получаем permissions для пользователя
        user_permissions = Permission.objects.filter(
            content_type=user_content_type,
            codename__in=[
                'add_customuser',
                'view_customuser'
            ]
        )

        # Объединяем все permissions
        all_permissions = user_permissions | task_permissions

        # Назначаем права группе
        manager_group.permissions.set(all_permissions)

        self.stdout.write(f'Назначено {all_permissions.count()} прав группе')

        # Выводим список прав
        self.stdout.write('Права группы:')
        for perm in all_permissions:
            self.stdout.write(f'    - {perm.name}')

        return manager_group

    def create_superuser(self):
        """Создание суперпользователя"""
        self.stdout.write('Создание суперпользователя...')

        superuser_email = 'admin@example.com'

        # Проверяем, существует ли уже суперпользователь
        if CustomUser.objects.filter(email=superuser_email).exists():
            superuser = CustomUser.objects.get(email=superuser_email)
            self.stdout.write(f'Суперпользователь уже существует: {superuser.email}')
            return superuser

        # Создаем суперпользователя
        superuser = CustomUser.objects.create_superuser(
            email=superuser_email,
            first_name='Admin',
            last_name='Admin',
            patronymic='Admin',
            work_position='System Administrator',
            department='IT',
            password='Password12'
        )

        self.stdout.write(f'Суперпользователь создан: {superuser.email}')
        self.stdout.write('Пароль: Password12')

        return superuser

    def create_test_users(self, count, manager_group):
        """Создание тестовых пользователей"""
        self.stdout.write(f'Создание {count} тестовых пользователей...')

        users = []

        # Данные для генерации пользователей
        first_names = ['Иван', 'Петр', 'Сидор', 'Семен', 'Андрей', 'Виктор', 'Алексей', 'Дмитрий', 'Кирилл', 'Олег']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Соколов', 'Михайлов',
                      'Федоров']
        patronymics = ['Иванович', 'Петрович', 'Сидорович', 'Александрович', 'Дмитриевич', 'Павлович']
        positions = ['Менеджер', 'Разработчик', 'Аналитик', 'Тестировщик', 'Дизайнер', 'Администратор']
        departments = ['IT', 'HR', 'Finance', 'Marketing', 'Sales', 'Operations']

        for i in range(count):
            # Генерируем уникальный email
            email = f"user{i + 1}@example.com"

            # Проверяем, не существует ли уже такой пользователь
            if CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.get(email=email)
                self.stdout.write(f'Пользователь {email} уже существует')
                users.append(user)
                continue

            # Создаем пользователя
            user = CustomUser.objects.create_user(
                email=email,
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                patronymic=random.choice(patronymics),
                work_position=random.choice(positions),
                department=random.choice(departments),
                password='User1234'
            )

            # Каждого третьего пользователя делаем менеджером
            if i % 3 == 0:
                user.groups.add(manager_group)
                self.stdout.write(f'Создан менеджер: {user.email}')
            else:
                self.stdout.write(f'Создан пользователь: {user.email}')

            users.append(user)

        self.stdout.write(f'Создано {len(users)} пользователей')
        self.stdout.write('Пароль для всех: User1234')

        return users

    def create_test_tasks(self, count, users, superuser):
        """Создание тестовых задач"""
        self.stdout.write(f'Создание {count} тестовых задач...')

        tasks = []

        # Статусы задач
        statuses = ['created', 'started']

        # Заголовки задач
        titles = [
            'Разработать API',
            'Написать документацию',
            'Провести код-ревью',
            'Исправить баги',
            'Обновить зависимости',
            'Настроить сервер',
            'Создать отчет',
            'Провести встречу',
            'Подготовить презентацию',
            'Протестировать функционал',
            'Оптимизировать запросы',
            'Обновить интерфейс',
            'Написать тесты',
            'Настроить CI/CD',
            'Провести рефакторинг',
            'Собрать требования',
            'Создать макеты',
            'Написать миграции',
            'Обновить документацию',
            'Провести аудит'
        ]

        # Описания задач
        descriptions = [
            'Необходимо разработать REST API для новой функциональности',
            'Обновить документацию в соответствии с последними изменениями',
            'Провести код-ревью пул-реквестов команды',
            'Исправить критические баги в продакшене',
            'Обновить зависимости проекта до актуальных версий',
            'Настроить сервер для деплоя приложения',
            'Создать отчет по результатам спринта',
            'Провести встречу с заказчиком для уточнения требований',
            'Подготовить презентацию для демо',
            'Протестировать новый функционал перед релизом'
        ]

        for i in range(count):
            # Выбираем случайных пользователей
            task_manager = random.choice([superuser] + users)
            executor = random.choice(users + [None])  # исполнитель может быть не назначен

            # Выбираем родительскую задачу (иногда)
            parent = None
            if tasks and i > 0 and random.random() > 0.7:
                parent = random.choice(tasks[:i])

            # Генерируем даты
            created_at = timezone.now() - timedelta(days=random.randint(1, 30))
            days_to_complete = random.randint(1, 14)
            date_to_complete = created_at + timedelta(days=days_to_complete)

            # Создаем задачу
            task = Task.objects.create(
                title=random.choice(titles),
                task_manager=task_manager,
                parent=parent,
                executor=executor,
                days_to_complete=days_to_complete,
                date_to_complete=date_to_complete,
                status=random.choice(statuses),
                task_description=random.choice(descriptions),
                created_at=created_at
            )

            tasks.append(task)

            # Выводим информацию о созданной задаче
            executor_name = executor.email if executor else 'Не назначен'
            self.stdout.write(
                f'Задача {i + 1}: "{task.title[:30]}..." - '
                f'Менеджер: {task_manager.email}, Исполнитель: {executor_name}'
            )

        self.stdout.write(f'Создано {len(tasks)} задач')

        return tasks

    def print_statistics(self, manager_group, users, tasks):
        """Вывод статистики"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА'))
        self.stdout.write('=' * 50)

        # Статистика по группам
        self.stdout.write('\nСТАТИСТИКА:')
        self.stdout.write(f'  • Группа "Manager": {manager_group.permissions.count()} прав')

        # Статистика по пользователям
        self.stdout.write('\nПОЛЬЗОВАТЕЛИ:')
        self.stdout.write(f'  • Всего: {CustomUser.objects.count()}')
        self.stdout.write(f'  • Суперпользователи: {CustomUser.objects.filter(is_superuser=True).count()}')
        self.stdout.write(f'  • Менеджеры: {CustomUser.objects.filter(groups=manager_group).count()}')

        # Статистика по задачам
        self.stdout.write('\nЗАДАЧИ:')
        self.stdout.write(f'  • Всего: {Task.objects.count()}')
        self.stdout.write(f'  • Созданы: {Task.objects.filter(status="created").count()}')
        self.stdout.write(f'  • В работе: {Task.objects.filter(status="started").count()}')
        self.stdout.write(f'  • Просрочены: {Task.objects.filter(status="overdue").count()}')
        self.stdout.write(f'  • Завершены: {Task.objects.filter(status="stoped").count()}')

        # Информация для входа
        self.stdout.write('\nДАННЫЕ ДЛЯ ВХОДА:')
        self.stdout.write('  • Суперпользователь: admin@example.com / Password12')
        self.stdout.write('  • Тестовый пользователь: user1@example.com / User1234')
        self.stdout.write('  • Тестовый менеджер: user2@example.com / User1234')

        self.stdout.write('\nГотово! Можно использовать команду: python manage.py init_data --help')
