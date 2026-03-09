from django.db import models
from crm.models import Contact

class Campaign(models.Model):
    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    content = models.TextField(help_text="The message template or content")
    schedule_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CampaignMessage(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='messages')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, SENT, DELIVERED, FAILED
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.campaign.name} - {self.contact.email}"
