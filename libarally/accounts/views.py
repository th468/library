from django.shortcuts import render,redirect
from .forms import UserCreationForm, UserLoginForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required




def regist(request):
    user_form = UserCreationForm(request.POST or None)
    if user_form.is_valid():
        user_form.save()
    return render(request, "accounts/registration.html", context={
            "user_form": user_form,
    })


def login_view(request):
    login_form = UserLoginForm(request.POST or None)
    next_url = request.GET.get("next")
    if login_form.is_valid():
        email = login_form.cleaned_data.get("email")
        password = login_form.cleaned_data.get("password")
        user = authenticate(request, email=email,password=password )
        print(f"Debug: User found -> {user}")
        if user is not None and user.is_authenticated:
            login(request, user)
            #ネクスト処理
            if next_url:
                redirect_url = next_url
            else:
                redirect_url = "accounts:index"
            return redirect(redirect_url)
        else:
            login_form.add_error("email", "ログインに失敗しました")


    return render(request,"accounts/login.html", context={
        "login_form": login_form,
    })

def index(request):
    return render(request, "accounts/index.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")

@login_required
def info(request):
    return render(request, "accounts/info.html")