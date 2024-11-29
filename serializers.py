# serializers.py
from rest_framework import serializers
from .models import Employee, TimeRecord, LeaveRequest
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Employee
        fields = ('id', 'user', 'annual_leave_balance', 'start_date')
        read_only_fields = ('id', 'start_date')

class TimeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRecord
        fields = ('id', 'employee', 'date', 'entry_time', 'exit_time', 'is_late', 'late_minutes')
        read_only_fields = ('id', 'is_late', 'late_minutes')

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ('id', 'employee', 'start_date', 'end_date', 'reason', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data
