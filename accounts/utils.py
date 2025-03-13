from django.core.mail import send_mail
from django.conf import settings

def send_status_email(user_email, subject, message):
    """
    Sends an email to the user with the given subject and message.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )
    
