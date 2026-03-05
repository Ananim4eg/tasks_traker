from django.urls import path
from rest_framework.routers import DefaultRouter


from task.apps import TaskConfig
from task.views import TaskViewSet, ImportantTaskView

app_name = TaskConfig.name

router = DefaultRouter()
router.register(r"task", TaskViewSet, basename="task")

urlpatterns = [
    path("important-tasks/", ImportantTaskView.as_view(), name="important-tasks"),
] + router.urls
