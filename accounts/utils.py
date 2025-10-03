from django.core.mail import send_mail
from django.conf import settings
import random
from django.core.mail import send_mail # Example import

def generate_otp():
    """Generates a 4-digit OTP as a string."""
    return str(random.randint(1000, 9999))



def send_otp_via_email(email, otp):
    subject = 'Your account verification email'
    message = f'Your OTP for registration is: {otp}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        return False
    
  