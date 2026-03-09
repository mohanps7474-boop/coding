from django import forms
from .models import Campaign

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['name', 'channel', 'content', 'schedule_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Campaign Name'}),
            'channel': forms.Select(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Write your message or template here...', 'rows': 5}),
            'schedule_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }
