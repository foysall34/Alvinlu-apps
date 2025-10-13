# api/urls.py

from django.urls import path, include
from .views import TaskAPIView, GeneratePdfApiView  , TaskDateView , TaskBoilerViewSet ,FilterClientTasksByDateView ,GenerateTaskReportView , ClientLatestTasksView,DashboardAnalyticsView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


router.register(r'boiler-plate', TaskBoilerViewSet, basename='taskboiler')
urlpatterns = [
    path('', include(router.urls)),
    path('tasks/', TaskAPIView.as_view(), name='task-create'),
    path('pdf/', GeneratePdfApiView.as_view(), name='generate-pdf'),
    path('get-all-date/', TaskDateView.as_view(), name='task-list'),
    path('tasks/filter-by-date/', FilterClientTasksByDateView.as_view(), name='filter-tasks-by-date'),
    path('report-pdf/', GenerateTaskReportView.as_view(), name='generate-task-report'),
    path('forme/', ClientLatestTasksView.as_view(), name='client-latest-tasks'),
    path('dashboard/analytics/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
]