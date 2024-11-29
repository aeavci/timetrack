from celery import shared_task
from django.core.mail import send_mail
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def notify_late_arrival(employee_id):
    # Send email notification
    employee = Employee.objects.get(id=employee_id)
    send_mail(
        'Late Arrival Notification',
        f'Employee {employee.user.username} has arrived late.',
        'from@example.com',
        ['manager@example.com'],
        fail_silently=False,
    )
    
    # Send WebSocket notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "notification.message",
            "message": f"Employee {employee.user.username} has arrived late"
        }
    )
