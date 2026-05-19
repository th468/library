from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserCreationForm, UserLoginForm


def regist(request):
    user_form = UserCreationForm(request.POST or None)
    if user_form.is_valid():
        user_form.save()
    return render(request, "accounts/registration.html", context={
            "form": user_form,
    })


def login_view(request):
    login_form = UserLoginForm(request.POST or None)

    next_url = request.GET.get("next") or request.POST.get("next")

    if login_form.is_valid():
        email = login_form.cleaned_data.get("email")
        password = login_form.cleaned_data.get("password")
        user = authenticate(request, email=email,password=password)

        if user is not None and user.is_authenticated:
            login(request, user)
            #ネクスト処理
            if next_url:
                redirect_url = next_url
            else:
                redirect_url = "accounts:index"
            return redirect(redirect_url)
        else:
            login_form.add_error(None, "ログインに失敗しました")


    return render(request,"accounts/login.html", context={
        "form": login_form,
        "next_url": next_url
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
