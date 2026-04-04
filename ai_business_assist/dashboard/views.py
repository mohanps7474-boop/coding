from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from crm.models import Contact
from campaigns.models import Campaign

from ai_business_assist.ai_utils import generate_ai_content

@login_required
def dashboard(request):
    total_contacts = Contact.objects.count()
    total_campaigns = Campaign.objects.count()
    
    context = {
        'total_contacts': total_contacts,
        'total_campaigns': total_campaigns,
    }
    return render(request, 'dashboard/index.html', context)

from crm.models import Contact
from accounts.utils import send_custom_email

@login_required
def ai_assistant(request):
    """
    View to interact with the AI Assistant using Gemini API.
    """
    ai_response = None
    error_msg = None
    if request.method == "POST":
        business_details = request.POST.get("business_details")
        goal = request.POST.get("goal")
        
        prompt = (
            f"You are BizBot, an expert marketing assistant. "
            f"Business Details: {business_details}. "
            f"Goal: {goal}. "
            f"Please generate 3 different marketing message options (one for Email, one for SMS, and one for Social Media). "
            f"Keep them professional, persuasive, and use a friendly tone."
        )
        
        ai_response = generate_ai_content(prompt)
        if not ai_response:
            error_msg = "AI service is temporarily unavailable. This may be due to API quota limits. Please try again in a few minutes."
    
    return render(request, 'dashboard/ai_assistant.html', {'ai_response': ai_response, 'error_msg': error_msg})

import re, uuid
from django.utils import timezone

@login_required
def chatbot_view(request):
    """
    ChatGPT-style chatbot with multi-conversation session management.
    Supports queries via POST or GET (for integration links).
    """
    conversations = request.session.get('conversations', {})
    current_id    = request.session.get('current_conv_id', None)

    # Action: New Chat
    if request.method == 'GET' and request.GET.get('action') == 'new':
        current_id = str(uuid.uuid4())
        conversations[current_id] = {
            'title': 'New Chat',
            'messages': [],
            'created': timezone.now().strftime('%b %d, %H:%M'),
        }
        request.session['conversations'] = conversations
        request.session['current_conv_id'] = current_id
        from django.shortcuts import redirect
        return redirect('chatbot')

    # Action: Switch conversation
    if request.method == 'GET' and request.GET.get('conv'):
        cid = request.GET.get('conv')
        if cid in conversations:
            request.session['current_conv_id'] = cid
            request.session.modified = True
            from django.shortcuts import redirect
            return redirect('chatbot')

    # Ensure a default conversation exists
    if not current_id or current_id not in conversations:
        current_id = str(uuid.uuid4())
        conversations[current_id] = {
            'title': 'New Chat',
            'messages': [],
            'created': timezone.now().strftime('%b %d, %H:%M'),
        }
        request.session['conversations'] = conversations
        request.session['current_conv_id'] = current_id

    chat_history = conversations[current_id]['messages']

    # --- Support Query from either POST or GET ---
    user_query = None
    if request.method == 'POST':
        user_query = request.POST.get('query', '').strip()
    elif request.method == 'GET' and 'query' in request.GET:
        user_query = request.GET.get('query', '').strip()

    if user_query:
        target_email = None
        contact_name = 'Valued Customer'
        bot_reply    = None

        # ── Step 1: Check if query contains a raw email address ──────────
        found_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_query)
        if found_emails:
            target_email = found_emails[0]
            contact = Contact.objects.filter(email=target_email).first()
            if contact:
                contact_name = f'{contact.first_name} {contact.last_name}'

        # ── Step 2: Only try name-lookup if the query looks like an email intent ──
        EMAIL_KEYWORDS = ['send', 'email', 'mail', 'message', 'write', 'compose', 'contact', 'follow up', 'reach out', 'notify', 'inform']
        looks_like_email_intent = any(kw in user_query.lower() for kw in EMAIL_KEYWORDS)

        if not target_email and looks_like_email_intent:
            extract_name_prompt = (
                f"User Query: '{user_query}'. "
                "Is the user referring to a specific person or customer by name? "
                "If yes, return ONLY that name (e.g. 'John Smith'). "
                "If you cannot find a clear person's name, return exactly: NONE"
            )
            extracted_name = generate_ai_content(extract_name_prompt)
            if extracted_name and extracted_name.strip().upper() != 'NONE':
                from django.db.models import Q
                name_clean = extracted_name.strip()
                contact = Contact.objects.filter(
                    Q(first_name__icontains=name_clean) |
                    Q(last_name__icontains=name_clean)
                ).first()
                if contact:
                    target_email = contact.email
                    contact_name = f'{contact.first_name} {contact.last_name}'

        # ── Step 3: Email drafting path ──────────────────────────────────
        if target_email:
            # Context for email drafting
            email_prompt = (
                f"Date: {timezone.now().strftime('%B %d, %Y')}\n"
                f"User request: '{user_query}'. "
                f"Target Customer: {contact_name} ({target_email}). "
                "Generate a professional, warm, and appropriate email response. "
                "Start with 'Subject: ...' followed by the body."
            )
            ai_generated_email = generate_ai_content(email_prompt)
            if ai_generated_email:
                lines   = ai_generated_email.split('\n')
                subject = 'Update from BizBot'
                body    = ai_generated_email
                for line in lines:
                    if line.startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                        body    = '\n'.join(lines[lines.index(line)+1:]).strip()
                        break
                from django.urls import reverse
                from urllib.parse import urlencode
                params      = {'recipient': target_email, 'subject': subject, 'message': body}
                preview_url = f"{reverse('gmail_view')}?{urlencode(params)}"
                bot_reply = {
                    'role': 'bot',
                    'content': f"I've found **{contact_name}** in your CRM and drafted an email. Click below to review and send:",
                    'is_action': True,
                    'action_link': preview_url,
                    'action_text': 'Review & Send Email',
                    'action_details': f'Recipient: {contact_name}\nAddress: {target_email}\nSubject: {subject}',
                }
            else:
                bot_reply = {'role': 'bot', 'content': 'I found the customer but had trouble generating the email. Please try again.'}

        # ── Step 4: General AI assistant (default path) ──────────────────
        if bot_reply is None:
            # Provide conversation history context
            context_str = ""
            for msg in chat_history[-6:]:
                 role_name = "User" if msg['role'] == 'user' else "Assistant"
                 context_str += f"{role_name}: {msg['content']}\n"
            
            general_prompt = (
                f"Current Date: {timezone.now().strftime('%B %d, %Y')}\n"
                "You are BizBot, a helpful and knowledgeable AI assistant. "
                "Answer ALL types of questions clearly and accurately — maths, general knowledge, business advice, coding, etc. "
                "If the user wants to send an email to a CRM contact but hasn't provided a name or email address, ask for those details. "
                f"\n\nRecent Conversation:\n{context_str}"
                f"User: {user_query}\nAssistant:"
            )
            ai_answer = generate_ai_content(general_prompt)
            bot_reply = {
                'role': 'bot',
                'content': ai_answer if ai_answer else "I'm sorry, I couldn't get a response right now. Please try again in a moment.",
            }

        chat_history.append({'role': 'user', 'content': user_query})
        chat_history.append(bot_reply)

        # Auto-title from first user message
        if len(chat_history) == 2:
            conversations[current_id]['title'] = (user_query[:40] + '…') if len(user_query) > 40 else user_query

        conversations[current_id]['messages'] = chat_history[-40:]
        request.session['conversations']      = conversations
        request.session['current_conv_id']    = current_id

    contacts = Contact.objects.all().values('pk', 'first_name', 'last_name', 'email')

    # Build sidebar list sorted newest-first
    conv_list = sorted(
        [{'id': k, **v} for k, v in conversations.items()],
        key=lambda x: x['created'], reverse=True
    )

    return render(request, 'dashboard/chatbot.html', {
        'chat_history': chat_history,
        'crm_contacts': contacts,
        'conv_list':    conv_list,
        'current_id':   current_id,
    })


@login_required
def clear_chat_history(request):
    """Wipes all conversations from the session."""
    request.session['conversations']   = {}
    request.session['current_conv_id'] = None
    from django.shortcuts import redirect
    return redirect('chatbot')


@login_required
@require_POST
def send_bulk_email(request):
    """
    Sends a personalised AI-generated (or custom) email to all selected CRM contacts.
    Expects POST fields: contact_pks (comma-separated), subject, message
    """
    from accounts.utils import send_custom_email

    pk_list = request.POST.get('contact_pks', '')
    subject  = request.POST.get('subject', 'A message from BizBot').strip()
    message  = request.POST.get('message', '').strip()

    if not pk_list:
        return JsonResponse({'success': False, 'error': 'No contacts selected.'}, status=400)

    pks = [p.strip() for p in pk_list.split(',') if p.strip()]
    contacts = Contact.objects.filter(pk__in=pks)

    if not contacts.exists():
        return JsonResponse({'success': False, 'error': 'No valid contacts found.'}, status=400)

    sent_to = []
    failed  = []

    for contact in contacts:
        contact_name = f"{contact.first_name} {contact.last_name}"
        # Personalise via AI if message provided, otherwise use raw message
        if message:
            personalise_prompt = (
                f"Personalise this message for {contact_name}: '{message}'. "
                "Keep it professional and warm. Do NOT add a subject line."
            )
            body = generate_ai_content(personalise_prompt) or message
        else:
            body = f"Hello {contact_name},\n\nThis is a message from BizBot.\n\nBest regards,\nThe BizBot Team"

        ok, err = send_custom_email(contact.email, subject, body)
        if ok:
            sent_to.append(contact.email)
        else:
            failed.append({'email': contact.email, 'error': err})

    return JsonResponse({
        'success': True,
        'sent_count': len(sent_to),
        'sent_to': sent_to,
        'failed': failed,
    })


@login_required
def analytics_view(request):
    """
    Renders simplified Analytics matching dashboard style with a barebones chart.
    """
    import random
    from datetime import timedelta
    from django.utils import timezone
    from crm.models import Contact
    from campaigns.models import Campaign
    
    total_contacts = Contact.objects.count()
    total_campaigns = Campaign.objects.count()
    
    mock_views = max(total_campaigns * total_contacts, 1500)
    mock_clicks = int(mock_views * random.uniform(0.15, 0.35))
    mock_rate = round((mock_clicks / mock_views) * 100, 1) if mock_views > 0 else 0
    
    dates = [(timezone.now() - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
    values = [int(mock_views * (random.uniform(0.1, 0.4)) / 7) for _ in range(7)]

    context = {
        'mock_views': mock_views,
        'mock_clicks': mock_clicks,
        'mock_rate': mock_rate,
        'dates_json': dates,
        'values_json': values,
    }
    return render(request, 'dashboard/analytics.html', context)
