from django.core.mail import send_mail
from django.conf import settings

def send_welcome_email(recipient_email):
    """
    Sends a welcome email to the newly registered user.
    """
    subject = 'Welcome to BizBot'
    message = 'Thank you for joining BizBot. Your journey to smarter business management starts here.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_custom_email(recipient_email, subject, message):
    """
    Sends a custom email and returns (success, error_msg)
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return True, None
    except Exception as e:
        error_msg = str(e)
        print(f"Error sending custom email: {error_msg}")
        return False, error_msg
