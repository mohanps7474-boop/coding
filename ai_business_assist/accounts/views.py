from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login as django_login,logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .utils import send_welcome_email
from .models import Profile



# Create your views here.
def handle_login(request):
    if request.user.is_authenticated:
        return redirect("contact_list")
    if request.method == "GET":
        success_msg = None
        if request.session.pop('registration_success', False):
            success_msg = "User Registered Successfully. Please log in."
        return render(request,"accounts/login.html", {"success": success_msg})
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        login_result = authenticate(username = email, password = password)
        if login_result:
            django_login(request,user=login_result)
            is_new_user = request.session.pop('is_new_user', False)
            if is_new_user:
                return redirect("form_page")
            return redirect("contact_list")
        else:
            return render(request,"accounts/login.html",{"error":"Invalid email or password"})
        
        
def register(request):
    if request.user.is_authenticated:
        return redirect("contact_list")
    if request.method == "GET":
        return render(request,"accounts/register.html")
    if request.method == "POST":
        first_name = request.POST.get('f_name')
        last_name = request.POST.get('l_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        conf_password = request.POST.get('conf_password')
        
        password_match_error = validate_password(password,conf_password)
        if password_match_error:
            return render(request,"accounts/register.html",{'error':password_match_error})

        try:
            existing_user = User.objects.get(email=email)
            return render(request,"accounts/register.html",{'error':"This email is already registered. Please login."})
        except User.DoesNotExist:
            try:
                # Use email as username as well based on your code
                User.objects.create_user(username=email,email=email,first_name=first_name,last_name=last_name,password=password)
                request.session['is_new_user'] = True
                request.session['registration_success'] = True
                
                # Send welcome email using the utility
                send_welcome_email(email)
                
                return redirect("login_page")
            except Exception as e:
                return render(request,"accounts/register.html",{'error':str(e)})
        
@login_required
def dashboard_view(request):
    # Note: named dashboard_view to avoid conflict if 'dashboard' is an app name
    return render(request,"accounts/dashboard.html")

@login_required
def front_page(request):
    return render(request,"accounts/front.html")

def landing_view(request):
    return render(request, "accounts/landing.html")

@login_required
def form_page(request):
    if request.method == "POST":
        # Get data from POST
        user_name = request.POST.get('user_name')
        shop_name = request.POST.get('shop_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        contact = request.POST.get('contact')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        shop_profile = request.FILES.get('shop_profile')

        # Update base User fields if changed
        if user_name:
            names = user_name.split(' ', 1)
            request.user.first_name = names[0]
            if len(names) > 1:
                request.user.last_name = names[1]
            request.user.save()

        # Update or create profile
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.shop_name = shop_name
        profile.address = address
        profile.contact = contact
        if lat:
            profile.latitude = lat
        if lng:
            profile.longitude = lng
        if shop_profile:
            profile.shop_profile = shop_profile
        profile.save()

        return redirect("front_page")
    return render(request, "accounts/form.html")

def handle_logout(request):
    logout(request)
    return redirect("handle_login")

def validate_password(password,conf_password):
    if password != conf_password:
        return "Passwords do not match"

    if len(password) < 8:
        return "Password should be of atleast 8 Charectors"

    contains_alphabet = False
    contains_number = False
    contains_char = False
    contains_caps = False
    contains_small = False
    for char in password:
        if char.isalpha():
            contains_alphabet = True
            if char.isupper():
                contains_caps = True
            if char.islower():
                contains_small = True
        if char.isdigit():
            contains_number = True
        if not char.isalpha() and not char.isdigit():
            contains_char = True

    if contains_alphabet == False or contains_number == False or contains_char == False or contains_caps == False or contains_small == False:
        return "Password should be a combination of alphabates,numbers and spcial charecters and one uppercase and lowercase letter."

@login_required
def test_email_view(request):
    """
    View to manually test email sending to the currently logged in user.
    """
    from .utils import send_welcome_email
    email_success = send_welcome_email(request.user.email)
    if email_success:
        return render(request, "accounts/dashboard.html", {"message": "Test email sent successfully to your registered email!"})
    else:
        return render(request, "accounts/dashboard.html", {"error": "Failed to send test email. Please check your SMTP settings."})

@login_required
def gmail_view(request):
    """
    View to send a custom email using Gmail SMTP.
    Supports GET parameters for pre-filling the form from the Chatbot.
    """
    context = {
        'recipient': request.GET.get('recipient', ''),
        'subject': request.GET.get('subject', ''),
        'message': request.GET.get('message', ''),
    }

    if request.method == "POST":
        recipient = request.POST.get("recipient")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        
        from .utils import send_custom_email
        success, error_msg = send_custom_email(recipient, subject, message)
        if success:
            context["success"] = f"Email successfully sent to {recipient}!"
        else:
            context["error"] = f"Failed to send email. SMTP Error: {error_msg}"
            
    return render(request, "accounts/gmail.html", context)
@login_required
def settings_view(request):
    """
    View for Account Management, Security, and App Information.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    context = {
        'user': request.user,
        'profile': profile,
        'active_tab': request.GET.get('tab', 'account')
    }
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.save()
            
            # Update extended profile fields
            profile.shop_name = request.POST.get('shop_name', profile.shop_name)
            profile.contact = request.POST.get('contact', profile.contact)
            profile.address = request.POST.get('address', profile.address)
            
            lat = request.POST.get('latitude')
            lng = request.POST.get('longitude')
            if lat: profile.latitude = lat
            if lng: profile.longitude = lng
            
            if 'shop_profile' in request.FILES:
                profile.shop_profile = request.FILES['shop_profile']
                
            profile.save()
            context['success'] = "Profile updated successfully."
            
        elif action == 'update_email':
            new_email = request.POST.get('email')
            if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                context['error'] = "This email is already in use by another account."
            else:
                request.user.email = new_email
                request.user.username = new_email # Since your app uses email as username
                request.user.save()
                context['success'] = "Email updated successfully."
                
        elif action == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            p1 = request.POST.get('new_password')
            p2 = request.POST.get('conf_password')
            
            pwd_error = validate_password(p1, p2)
            if pwd_error:
                context['error'] = pwd_error
            else:
                request.user.set_password(p1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                context['success'] = "Password changed successfully."
                
        elif action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            return redirect('handle_login')

    return render(request, "accounts/settings.html", context)

def about_view(request):
    return render(request, "accounts/about.html")
