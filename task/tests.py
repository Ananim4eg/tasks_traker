from datetime import timedelta

from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import status
from rest_framework.fields import DateTimeField
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from task.models import Task
from users.models import CustomUser


class TaskTestCase(APITestCase):

    def setUp(self):
        url_user = reverse('users:register')
        data_user = {
            "email": "ivanov@example.com",
            "password": "Password12",
            "confirm_password": "Password12",
            "first_name": "Иван",
            "last_name": "Иванов",
            "patronymic": "Иванович",
            "work_position": "Бухгалтер",
        }
        response_user = self.client.post(url_user, data_user)
        self.assertEqual(response_user.status_code, status.HTTP_201_CREATED)

        url_manager = reverse('users:register')
        data_manager = {
            "email": "manager@example.com",
            "password": "Password12",
            "confirm_password": "Password12",
            "first_name": "manager",
            "last_name": "manager",
            "patronymic": "manager",
            "work_position": "manager",
        }

        response_manager = self.client.post(url_manager, data_manager)
        self.assertEqual(response_manager.status_code, status.HTTP_201_CREATED)

        self.user = CustomUser.objects.get(email="ivanov@example.com")
        self.manager = CustomUser.objects.get(email="manager@example.com")
        self.manager_group, created = Group.objects.get_or_create(name='manager')
        self.manager.groups.add(self.manager_group)
        self.client.force_authenticate(user=self.user)

        url = reverse("task:task-list")
        data = {
            'title': 'Расчеты',
            'executor': self.user.pk,
            'days_to_complete': 5,
            'task_description': 'Расчет бюджета'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.task = Task.objects.get(title='Расчеты')

    def test_task_retrieve(self):
        url = reverse("task:task-detail", args=(self.task.pk,))
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("title"), self.task.title)

    def test_task_create(self):
        url = reverse("task:task-list")
        data = {
            'title': 'Расчеты затрат',
            'executor': self.user.pk,
            'days_to_complete': 4,
            'task_description': "Расчет бюджета"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.all().count(), 2)

    def test_task_update(self):
        url = reverse("task:task-detail", args=(self.task.pk,))
        data = {
            'title': 'Расчеты бюджета',
            'executor': self.user.pk,
            'days_to_complete': 6,
            'task_description': "Расчет бюджета"
        }
        response = self.client.patch(url, data)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("title"), 'Расчеты бюджета')

    def test_task_delete(self):
        url = reverse("task:task-detail", args=(self.task.pk,))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.all().count(), 0)

    def test_task_list(self):
        time_create = timezone.localtime(self.task.created_at)
        time_complete = timedelta(days=self.task.days_to_complete)
        url = reverse("task:task-list")
        response = self.client.get(url)
        data = response.json()
        result = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.task.pk,
                    "title": "Расчеты",
                    "task_manager": str(self.user),
                    "parent": None,
                    "executor": str(self.user),
                    "date_to_complete": (time_create + time_complete).strftime("%d-%m-%Y %H:%M"),
                    "status": "Запущена",
                    "task_description": "Расчет бюджета",
                    "created_at": DateTimeField(format="%d-%m-%Y %H:%M").to_representation(self.task.created_at),
                }
            ],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, result)

    def test_important_tasks(self):
        url = reverse('task:important-tasks')
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(data['detail'], 'У вас недостаточно прав для выполнения данного действия.')

    def test_important_tasks_manager(self):
        self.client.force_authenticate(user=self.manager)

        url_user_test_1 = reverse('users:register')
        data_user_test_1 = {
            "email": "test1@example.com",
            "password": "Password12",
            "confirm_password": "Password12",
            "first_name": "Тест",
            "last_name": "Тест",
            "patronymic": "Тест",
            "work_position": "tester",
        }
        response_user_test_1 = self.client.post(url_user_test_1, data_user_test_1)
        self.assertEqual(response_user_test_1.status_code, status.HTTP_201_CREATED)

        url_user_test_2 = reverse('users:register')
        data_user_test_2 = {
            "email": "test2@example.com",
            "password": "Password12",
            "confirm_password": "Password12",
            "first_name": "test",
            "last_name": "test",
            "patronymic": "test",
            "work_position": "tester",
        }
        response_user_test_2 = self.client.post(url_user_test_2, data_user_test_2)
        self.assertEqual(response_user_test_2.status_code, status.HTTP_201_CREATED)

        url = reverse("task:task-list")
        data = {
            'title': 'Проверка',
            'parent': self.task.pk,
            'executor': '',
            'days_to_complete': 3,
            'task_description': 'Тестовая задача'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.task_test = Task.objects.get(title='Проверка')

        time_create = self.task_test.created_at
        time_complete = timedelta(days=self.task_test.days_to_complete)

        url_important_task = reverse('task:important-tasks')
        response_important_task = self.client.get(url_important_task)
        data = response_important_task.json()
        result = {
            "count": 1,
            "ordering": "date_to_complete",
            "results": [
                {
                    "task": "Проверка",
                    "date_to_complete": (time_create + time_complete).strftime("%d-%m-%Y %H:%M"),
                    "executors": [
                        "manager manager manager",
                        "test test test",
                        "Тест Тест Тест",
                        "Иванов Иван Иванович"
                    ]
                }
            ]
        }
        data['results'].sort()
        result['results'].sort()
        self.assertEqual(response_important_task.status_code, HTTP_200_OK)
        self.assertEqual(data, result)
