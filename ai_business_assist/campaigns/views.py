from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Campaign
from .forms import CampaignForm

@login_required
def campaign_list(request):
    campaigns = Campaign.objects.all()
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})

@login_required
def campaign_create(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('campaign_list')
    else:
        form = CampaignForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form})
