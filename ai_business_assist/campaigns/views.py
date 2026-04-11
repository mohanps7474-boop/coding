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
            campaign = form.save(commit=False)
            # Auto-set to SCHEDULED if a future time is given, else DRAFT
            if campaign.schedule_time and campaign.schedule_time > timezone.now():
                campaign.status = 'SCHEDULED'
            campaign.save()
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
            campaign = form.save(commit=False)
            if campaign.schedule_time and campaign.schedule_time > timezone.now():
                campaign.status = 'SCHEDULED'
            campaign.save()
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
    AI Chatbot for campaign planning.
    Uses local IST time so suggestions match the user's clock.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '')

            # Use local time so AI suggestions match the user's clock
            local_now = timezone.localtime(timezone.now())
            # Default schedule = tomorrow at 10am
            default_schedule = (local_now.replace(hour=10, minute=0, second=0, microsecond=0)
                                + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')

            extract_prompt = (
                f"You are a marketing assistant. Create a campaign plan for: '{prompt}'.\n\n"
                "Respond with ONLY a single JSON object using these exact keys:\n"
                "  name     - short campaign name (string)\n"
                "  channel  - one of: EMAIL, SMS, WHATSAPP\n"
                "  content  - the full message body (string)\n"
                "  schedule - launch datetime in format YYYY-MM-DDTHH:MM\n\n"
                f"Today's date and time: {local_now.strftime('%Y-%m-%d %H:%M')} IST\n\n"
                "Example:\n"
                '{"name":"Summer Flash Sale","channel":"EMAIL","content":"Don\'t miss our Summer Flash Sale! Get 30% off all items today only. Shop now at our store.","schedule":"'
                + default_schedule + '"}\n\n'
                "Now write the JSON for the user request. No markdown, no explanation, ONLY the JSON object."
            )

            ai_raw = generate_ai_content(extract_prompt)
            print(f"DEBUG CAMPAIGN AI RAW: {ai_raw}")

            extracted = {}
            if ai_raw:
                # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
                cleaned = re.sub(r'```(?:json)?\s*', '', ai_raw).replace('```', '').strip()

                # Stage 1: Try to parse cleaned JSON
                json_match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
                if json_match:
                    try:
                        extracted = json.loads(json_match.group(1).strip())
                    except Exception:
                        pass

                # Stage 2: If content still missing, use full AI text as content
                if not extracted.get('content') or len(extracted.get('content', '')) < 5:
                    extracted['content'] = cleaned
                    # Try to find a Name: line
                    name_m = re.search(r'(?:name|campaign)[:\s]+([^\n\r"{}]+)', ai_raw, re.IGNORECASE)
                    if name_m:
                        extracted['name'] = name_m.group(1).strip().strip('"').strip("'")
                    # Try to find a channel keyword
                    for ch in ['EMAIL', 'SMS', 'WHATSAPP']:
                        if ch in ai_raw.upper():
                            extracted['channel'] = ch
                            break
                    # Try to find a date in the response
                    date_m = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', ai_raw)
                    if date_m:
                        extracted['schedule'] = date_m.group(1)

            # ── Stage 3: Final guaranteed fallbacks ──────────────────────────
            # Derive a sensible name from the user's prompt if AI didn't provide one
            if not extracted.get('name') or extracted['name'].strip() in ('', 'Untitled'):
                # Title-case the user's prompt (first 40 chars) as the name
                extracted['name'] = prompt.strip().title()[:50] or 'New Campaign'
            if not extracted.get('channel'):
                extracted['channel'] = 'EMAIL'
            if not extracted.get('content') or len(extracted.get('content', '')) < 5:
                extracted['content'] = f"Hello! We have an exciting offer for you. {prompt.strip().capitalize()}."
            if not extracted.get('schedule') or extracted['schedule'].strip().lower() in ('', 'immediate', 'now'):
                extracted['schedule'] = default_schedule

            print(f"DEBUG CAMPAIGN AI FINAL: {extracted}")
            return JsonResponse({'success': True, 'data': extracted})

        except Exception as e:
            print(f"CAMPAIGN AI FATAL: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST only'})


def _do_launch(campaign):
    """Internal helper: personalize & send emails for a campaign, then mark COMPLETED."""
    from .models import CampaignMessage
    from accounts.utils import send_custom_email

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
    return sent_count


@login_required
def campaign_launch(request, pk):
    """Immediately launches a DRAFT or SCHEDULED campaign on demand."""
    campaign = Campaign.objects.get(pk=pk)
    if campaign.status not in ('DRAFT', 'SCHEDULED'):
        return redirect('campaign_list')

    sent_count = _do_launch(campaign)

    from django.contrib import messages
    messages.success(request, f"Launched '{campaign.name}'! Sent personalized messages to {sent_count} contacts.")
    return redirect('campaign_list')


@login_required
def check_scheduled_campaigns(request):
    """
    Lightweight endpoint called every minute by the campaign list page.
    Finds all SCHEDULED campaigns whose schedule_time <= now() and launches them automatically.
    Returns JSON listing any campaigns that were triggered.
    """
    now = timezone.now()
    due = Campaign.objects.filter(status='SCHEDULED', schedule_time__lte=now)
    triggered = []
    for campaign in due:
        sent_count = _do_launch(campaign)
        triggered.append({'id': campaign.pk, 'name': campaign.name, 'sent': sent_count})
        print(f"[SCHEDULER] Auto-launched '{campaign.name}' at {now.strftime('%H:%M:%S %Z')} — sent to {sent_count} contacts.")

    return JsonResponse({
        'checked_at': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'triggered': triggered,
    })
