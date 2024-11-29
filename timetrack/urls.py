from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'timerecords', views.TimeRecordViewSet, basename='timerecord')
router.register(r'leaverequests', views.LeaveRequestViewSet, basename='leaverequest')

urlpatterns = [
    path('api/', include(router.urls)),
]