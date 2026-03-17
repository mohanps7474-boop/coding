from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login as django_login,logout
from django.contrib.auth.decorators import login_required


# Create your views here.
def handle_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
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
            return redirect("dashboard")
        else:
            return render(request,"accounts/login.html",{"error":"Invalid email or password"})
        
        
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
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

def portfolio_view(request):
    return render(request, "accounts/portfolio.html")

@login_required
def form_page(request):
    if request.method == "POST":
        # Process form data here if needed
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
