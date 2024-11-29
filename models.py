from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, time



def is_holiday(date):
    # Check if weekend
    if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return True
    return False

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    annual_leave_balance = models.FloatField(default=15.0)
    start_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username

class TimeRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    entry_time = models.TimeField()
    exit_time = models.TimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    late_minutes = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if is_holiday(self.date):
            raise ValidationError("Cannot create time record on holidays")
        if self.entry_time > time(8, 0):  # Company start time
            self.is_late = True
            time_diff = datetime.combine(self.date, self.entry_time) - \
                       datetime.combine(self.date, time(8, 0))
            self.late_minutes = time_diff.seconds // 60
        super().save(*args, **kwargs)

class LeaveRequest(models.Model):
    LEAVE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=LEAVE_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after start date")
        if self.employee.annual_leave_balance < (self.end_date - self.start_date).days:
            raise ValidationError("Insufficient leave balance")