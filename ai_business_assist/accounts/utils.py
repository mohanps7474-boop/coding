from django.core.mail import send_mail
from django.conf import settings
import imaplib, email
from email.header import decode_header
from ai_business_assist.ai_utils import generate_ai_content
from django.utils import timezone

def send_welcome_email(recipient_email):
    """
    Sends a welcome email to the newly registered user.
    """
    subject = 'Welcome to BizBot'
    message = 'Thank you for joining BizBot. Your journey to smarter business management starts here.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_custom_email(recipient_email, subject, message):
    """
    Sends a custom email and returns (success, error_msg)
    """
    from_name = "BizBot Business Assistant"
    from_email = f"{from_name} <{settings.EMAIL_HOST_USER}>"
    recipient_list = [recipient_email]
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True, None
    except Exception as e:
        error_msg = str(e)
        print(f"Error sending custom email: {error_msg}")
        return False, error_msg

def send_custom_sms(phone_number, message):
    """
    Simulated SMS sender.
    """
    if not phone_number: return False, "No phone number"
    print(f"\n[SMS SENT] To: {phone_number}\n[CONTENT] {message}\n")
    return True, None

def sync_inbox_and_reply():
    """
    Connects to Gmail via IMAP, finds unread replies from CRM contacts,
    analyzes them with AI, and sends an auto-reply.
    Returns (processed_count, error)
    """
    from crm.models import Contact, Interaction
    
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    
    if not user or not password:
        return 0, "Email credentials not configured"

    processed = 0
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK': return 0, "Could not search inbox"

        msg_ids = messages[0].split()
        for msg_id in msg_ids:
            res, msg_data = mail.fetch(msg_id, "(RFC822)")
            if res != 'OK': continue
            
            raw_email = msg_data[0][1]
            email_msg = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(email_msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
                
            from_raw = email_msg.get("From")
            from_email = email.utils.parseaddr(from_raw)[1].lower()
            
            contact = Contact.objects.filter(email=from_email).first()
            if not contact: continue
                
            ext_id = email_msg.get("Message-ID", str(msg_id))
            if Interaction.objects.filter(external_id=ext_id).exists(): continue
                
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_msg.get_payload(decode=True).decode()

            Interaction.objects.create(
                contact=contact, channel='EMAIL', direction='INBOUND',
                content=body, external_id=ext_id
            )

            # ── Sophisticated AI Auto-Reply Generation ──────────────────────
            reply_prompt = (
                f"You are the Business Assistant for a professional shop. "
                "Your goal is to handle customer service with extreme politeness and helpfulness.\n\n"
                f"CUSTOMER DETAILS:\n"
                f"- Name: {contact.first_name} {contact.last_name}\n"
                f"- Email: {from_email}\n\n"
                f"INCOMING MESSAGE:\n"
                f"Subject: {subject}\n"
                f"Body: {body}\n\n"
                "INSTRUCTIONS:\n"
                "1. Address the customer by their first name.\n"
                "2. If they have a question, provide a detailed and helpful answer.\n"
                "3. If they are providing feedback, thank them sincerely.\n"
                "4. If they have a complaint, be empathetic and offer to investigate further.\n"
                "5. Maintain a professional, warm, and expert tone.\n"
                "6. Sign off as 'Customer Support Team | BizBot'.\n\n"
                "Write the full email response now:"
            )
            ai_reply = generate_ai_content(reply_prompt)
            
            if ai_reply:
                ok, err = send_custom_email(from_email, f"Re: {subject}", ai_reply)
                if ok:
                    Interaction.objects.create(
                        contact=contact, channel='EMAIL', direction='OUTBOUND', content=ai_reply
                    )
                    processed += 1
                    
        mail.logout()
        return processed, None
    except Exception as e:
        print(f"IMAP SYNC ERROR: {e}")
        return processed, str(e)
