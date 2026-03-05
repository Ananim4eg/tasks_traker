from django.db.models import Prefetch, Count, Q

from task.models import Task
from users.models import CustomUser


def get_employees_load(statuses, ordering='active_tasks_count'):
    """Получаем загруженность сотрудников"""
    return CustomUser.objects.annotate(
        active_tasks_count=Count(
            'executor_task',
            filter=Q(executor_task__status__in=statuses)
        )
    ).prefetch_related(
        Prefetch(
            'executor_task',
            queryset=Task.objects.filter(status__in=statuses),
            to_attr='active_tasks_list'
        )
    ).order_by(ordering)


def get_important_tasks(ordering, statuses):
    """
    Запрос из БД задач, которые не взяты в работу (created),
    но от которых зависят другие задачи, взятые в работу (started)
    """

    return Task.objects.filter(
        status='created',
        parent__status__in=statuses
    ).select_related(
        'parent',
        'parent__executor'
    ).order_by(ordering)


def get_recommended_executor(task, first_five_least_loaded, employees_load):
    """
    Возвращает ФИО рекомендуемого исполнителя
    """
    min_load = first_five_least_loaded.first().active_tasks_count if first_five_least_loaded else 0

    parent_executor = task.parent.executor if task.parent and task.parent.executor else None

    list_employees = [str(emp) for emp in first_five_least_loaded]
    if not parent_executor:
        return list_employees

    parent_load = 0
    for employee in employees_load:
        if employee.id == parent_executor.id:
            parent_load = employee.active_tasks_count
            break

    if parent_load <= min_load + 2 and parent_executor not in first_five_least_loaded:
        return [str(parent_executor)]+list_employees
    else:
        return list_employees
