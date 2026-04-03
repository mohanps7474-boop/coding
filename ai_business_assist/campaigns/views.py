from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json, re
from ai_business_assist.ai_utils import generate_ai_content
from django.utils import timezone
from .models import Campaign
from .forms import CampaignForm
from crm.models import Contact

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

@login_required
def campaign_edit(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('campaign_list')
    else:
        form = CampaignForm(instance=campaign)
    return render(request, 'campaigns/campaign_form.html', {'form': form, 'editing': True})

@login_required
def campaign_delete(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    campaign.delete()
    return redirect('campaign_list')

@login_required
def campaign_ai_suggest(request):
    """
    Highly robust AI Chatbot for campaign planning.
    Optimized for smaller models like Gemma 3-1B and 2x series.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            
            # Use 'one-shot' example to force format on smaller models
            extract_prompt = (
                f"Identify a marketing plan from this request: '{prompt}'.\n\n"
                "RULES:\n"
                "- Pick a Channel: EMAIL, SMS, or WHATSAPP.\n"
                "- Create a Name.\n"
                "- Write the Message Body.\n"
                f"- Suggest a Launch Date (Current Time: {timezone.now().strftime('%Y-%m-%d %H:%M')}).\n\n"
                "EXAMPLE OUTPUT:\n"
                '{"name": "Diwali Sale", "channel": "EMAIL", "content": "Wish you a happy Diwali! Shop now.", "schedule": "2026-11-01T10:00"}\n\n'
                "Now return ONLY the JSON result for the user's request."
            )
            
            ai_raw = generate_ai_content(extract_prompt)
            print(f"DEBUG CAMPAIGN AI: {ai_raw}")

            extracted = {}
            if ai_raw:
                # Stage 1: Try strict JSON regex
                json_match = re.search(r'(\{.*\})', ai_raw, re.DOTALL)
                if json_match:
                    try:
                        extracted = json.loads(json_match.group(1).strip())
                    except:
                        pass
                
                # Stage 2: Keyword fallback parsing (Crucial for Gemma 3)
                if not extracted.get('content') or len(extracted.get('content', '')) < 5:
                    extracted['content'] = ai_raw
                    # Look for Name: [text]
                    name_m = re.search(r'Name:\s*(.*)', ai_raw, re.IGNORECASE)
                    extracted['name'] = name_m.group(1).strip() if name_m else "AI Recommended Plan"
                    # Look for Channel: [text]
                    for ch in ['EMAIL', 'SMS', 'WHATSAPP']:
                        if ch in ai_raw.upper():
                            extracted['channel'] = ch
                            break
                    # Look for Schedule/Date
                    date_m = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', ai_raw)
                    extracted['schedule'] = date_m.group(1) if date_m else timezone.now().strftime('%Y-%m-%dT%H:%M')
            
            return JsonResponse({'success': True, 'data': extracted})
            
        except Exception as e:
            print(f"CAMPAIGN AI FATAL: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'POST only'})

@login_required
def campaign_launch(request, pk):
    """
    Launches a draft campaign with AI Personalization.
    """
    from .models import CampaignMessage
    from accounts.utils import send_custom_email
    
    campaign = Campaign.objects.get(pk=pk)
    if campaign.status != 'DRAFT':
        return redirect('campaign_list')

    contacts = Contact.objects.all()
    campaign.status = 'RUNNING'
    campaign.save()

    sent_count = 0
    for contact in contacts:
        personalization_prompt = (
            f"Personalize this template: '{campaign.content}' for customer {contact.first_name}. "
            "Maintain the exact core offer but make it feel warm and specifically written for them. "
            "Return ONLY the message body."
        )
        personalized_content = generate_ai_content(personalization_prompt) or campaign.content

        msg_log = CampaignMessage.objects.create(campaign=campaign, contact=contact, status='PENDING')
        success, error_msg = send_custom_email(contact.email, f"Update: {campaign.name}", personalized_content)

        if success:
            msg_log.status = 'SENT'
            msg_log.sent_at = timezone.now()
            sent_count += 1
        else:
            msg_log.status = 'FAILED'
            msg_log.error_message = error_msg
        msg_log.save()

    campaign.status = 'COMPLETED'
    campaign.save()

    from django.contrib import messages
    messages.success(request, f"Launched '{campaign.name}'! Sent personalized messages to {sent_count} contacts.")
    return redirect('campaign_list')
