from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import time
from django.db.models import Q
from django_filters import rest_framework as filters
from .tasks import notify_late_arrival

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'employee')

class IsAuthorizedPersonnel(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='AuthorizedPersonnel').exists()

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.groups.filter(name='AuthorizedPersonnel').exists():
            return Employee.objects.all()
        return Employee.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def leave_balance(self, request):
        employee = request.user.employee
        return Response({'balance': employee.annual_leave_balance})

class TimeRecordViewSet(viewsets.ModelViewSet):
    serializer_class = TimeRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('date', 'is_late')

    def get_queryset(self):
        if self.request.user.groups.filter(name='AuthorizedPersonnel').exists():
            return TimeRecord.objects.all()
        return TimeRecord.objects.filter(employee=self.request.user.employee)

    @action(detail=False, methods=['post'])
    def checkin(self, request):
        employee = request.user.employee
        current_time = timezone.now().time()
        
        # Check if already checked in today
        if TimeRecord.objects.filter(
            employee=employee,
            date=timezone.now().date()
        ).exists():
            return Response(
                {"error": "Already checked in today"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        time_record = TimeRecord.objects.create(
            employee=employee,
            entry_time=current_time
        )
        
        # Check if late and notify if necessary
        if current_time > time(8, 0):
            notify_late_arrival.delay(employee.id)
        
        return Response(
            TimeRecordSerializer(time_record).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        employee = request.user.employee
        try:
            time_record = TimeRecord.objects.get(
                employee=employee,
                date=timezone.now().date(),
                exit_time__isnull=True
            )
            time_record.exit_time = timezone.now().time()
            time_record.save()
            return Response(TimeRecordSerializer(time_record).data)
        except TimeRecord.DoesNotExist:
            return Response(
                {"error": "No active check-in found"},
                status=status.HTTP_400_BAD_REQUEST
            )

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('status', 'start_date')

    def get_queryset(self):
        if self.request.user.groups.filter(name='AuthorizedPersonnel').exists():
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.filter(employee=self.request.user.employee)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not request.user.groups.filter(name='AuthorizedPersonnel').exists():
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leave_request = self.get_object()
        if leave_request.status != 'PENDING':
            return Response(
                {"error": "Can only approve pending requests"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = 'APPROVED'
        leave_request.save()
        
        # Deduct days from annual leave balance
        employee = leave_request.employee
        days_requested = (leave_request.end_date - leave_request.start_date).days + 1
        employee.annual_leave_balance -= days_requested
        employee.save()
        
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not request.user.groups.filter(name='AuthorizedPersonnel').exists():
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leave_request = self.get_object()
        leave_request.status = 'REJECTED'
        leave_request.save()
        return Response(LeaveRequestSerializer(leave_request).data)
