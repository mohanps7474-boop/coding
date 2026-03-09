import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_business_assist.settings')
django.setup()

from crm.models import Tag, Contact
from campaigns.models import Campaign

def populate_data():
    print("Populating initial data...")
    
    # Create Tags
    vip, _ = Tag.objects.get_or_create(name='VIP')
    lead, _ = Tag.objects.get_or_create(name='Lead')
    customer, _ = Tag.objects.get_or_create(name='Customer')
    
    # Create Contacts
    contacts_data = [
        ('James', 'Smith', 'james@example.com', '+1234567890', [vip, customer]),
        ('Maria', 'Garcia', 'maria@example.com', '+1234567891', [customer]),
        ('David', 'Miller', 'david@example.com', '+1234567892', [lead]),
        ('Sarah', 'Wilson', 'sarah@example.com', '+1234567893', [lead]),
    ]
    
    for first, last, email, phone, tags in contacts_data:
        contact, created = Contact.objects.get_or_create(
            email=email,
            defaults={'first_name': first, 'last_name': last, 'phone_number': phone}
        )
        if created:
            contact.tags.set(tags)
            print(f"Created contact: {email}")

    # Create Campaigns
    campaigns_data = [
        ('Summer Flash Sale', 'EMAIL', 'Get ready for our big summer flash sale! 20% off everything.', 'COMPLETED'),
        ('Welcome Series', 'WHATSAPP', 'Welcome to our business assist platform. We are glad to have you!', 'RUNNING'),
        ('Follow Up Promo', 'SMS', 'Revisit our store and get a free gift with your next purchase.', 'SCHEDULED'),
    ]

    for name, channel, content, status in campaigns_data:
        Campaign.objects.get_or_create(
            name=name,
            defaults={
                'channel': channel,
                'content': content,
                'status': status,
                'schedule_time': datetime.now() + timedelta(days=1)
            }
        )
        print(f"Created campaign: {name}")

    print("Data population complete!")

if __name__ == '__main__':
    populate_data()
