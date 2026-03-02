from rest_framework.routers import DefaultRouter


from task.apps import TaskConfig
from task.views import TaskViewSet

app_name = TaskConfig.name

router = DefaultRouter()
router.register(r"task", TaskViewSet, basename="task")

urlpatterns = [] + router.urls