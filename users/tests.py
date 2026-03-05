from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.models import CustomUser


class UsersTestCase(APITestCase):

    def setUp(self):
        url = reverse("users:register")
        data = {
            'email': 'test@example.com',
            'first_name': 'test',
            'last_name': 'testing',
            'patronymic': 'tested',
            'work_position': 'manager',
            'password': 'Password12',
            'confirm_password': 'Password12',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse("users:register")
        data = {
            'email': 'manager@example.com',
            'first_name': 'manager',
            'last_name': 'manager',
            'patronymic': 'manager',
            'work_position': 'tester',
            'password': 'Password12',
            'confirm_password': 'Password12',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.user = CustomUser.objects.get(email='test@example.com')
        self.manager = CustomUser.objects.get(email='manager@example.com')
        self.manager_group, created = Group.objects.get_or_create(name='manager')
        self.manager.groups.add(self.manager_group)

    def test_user_retrieve(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users:user_detail', args=(self.user.pk,))
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get('first_name'), self.user.first_name)

    def test_user_create(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:register")
        data = {
            'email': 'ivanov@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'patronymic': 'Иванович',
            'work_position': 'manager',
            'password': 'Password12',
            'confirm_password': 'Password12',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.all().count(), 3)

    def test_user_update(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users:user_update', args=(self.user.pk,))
        data = {
            'email': 'kirillov@example.com',
            'first_name': 'Кирилл',
            'last_name': 'Кириллов',
            'patronymic': 'Кириллович',
            'work_position': 'manager',
        }
        response = self.client.patch(url, data)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['first_name'], 'Кирилл')

    def test_user_delete(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:user_delete", args=(self.user.pk,))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'У вас недостаточно прав для выполнения данного действия.')

    def test_user_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users:user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'У вас недостаточно прав для выполнения данного действия.')

    def test_user_get_busy_employees(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('users:busy-employees')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'У вас недостаточно прав для выполнения данного действия.')

    def test_manage_update_user(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('users:user_update', args=(self.user.pk,))
        data = {
            'email': 'kirillov@example.com',
            'first_name': 'Кирилл',
            'last_name': 'Кириллов',
            'patronymic': 'Кириллович',
            'work_position': 'manager',
        }
        response = self.client.patch(url, data)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['non_field_errors'], ["У вас нет прав на изменение поля 'email'"])

    def test_manage_update_user_available_fields(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('users:user_update', args=(self.user.pk,))
        data = {
            'email': 'test@example.com',
            'first_name': 'test',
            'last_name': 'testing',
            'patronymic': 'tested',
            'work_position': 'IT'
        }
        response = self.client.patch(url, data)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['work_position'], 'IT')

    def test_manage_list_users(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('users:user_list')
        response = self.client.get(url)
        data = response.json()
        result = [
            {
                "id": self.manager.pk,
                "email": "manager@example.com",
                "first_name": "manager",
                "last_name": "manager",
                "patronymic": "manager",
                "work_position": "tester",
                "department": None
            },
            {
                "id": self.user.pk,
                "email": "test@example.com",
                "first_name": "test",
                "last_name": "testing",
                "patronymic": "tested",
                "work_position": "manager",
                "department": None
            }
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, result)

    def test_manager_delete_user(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse("users:user_delete", args=(self.user.pk,))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'У вас недостаточно прав для выполнения данного действия.')

    def test_manager_get_busy_employees(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('users:busy-employees')
        response = self.client.get(url)
        data = response.json()
        result = {
            'ordering': '-active_tasks_count',
            'count': 2,
            'results': [
                {
                    'id': self.manager.pk,
                    'work_position': 'tester',
                    'full_name': 'manager manager manager',
                    'active_tasks_count': 0,
                    'active_tasks': []
                },
                {
                    'id': self.user.pk,
                    'work_position': 'manager',
                    'full_name': 'testing test tested',
                    'active_tasks_count': 0,
                    'active_tasks': [],
                }
            ]
        }

        data['results'].sort(key=lambda x: x['id'])
        result['results'].sort(key=lambda x: x['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, result)
