from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from crm.models import Contact
from campaigns.models import Campaign

@login_required
def dashboard(request):
    total_contacts = Contact.objects.count()
    total_campaigns = Campaign.objects.count()
    recent_campaigns = Campaign.objects.order_by('-created_at')[:5]
    
    context = {
        'total_contacts': total_contacts,
        'total_campaigns': total_campaigns,
        'recent_campaigns': recent_campaigns,
    }
    return render(request, 'dashboard/index.html', context)
