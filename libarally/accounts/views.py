from django.shortcuts import render
from .forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# def user_list(request):
#     return render(
#         request, "UserApp/user_list.html"
#     )



def regist(request):
    user_form = UserCreationForm(request.POST or None)
    if user_form.is_valid():
        user = user_form.save(commit=False)
        password = user_form.creaned_data.get("password","")
        try:
            validate_password(password)
        except ValidationError as e:
            user_form.add_error("password, e")
            return render(request, "user/registration.html", context={
                "user_form":user_form,
            })
        user.set_password(password)
        user.save()
    return render(request, "accounts/registration.html", context={


        "user_form": user_form,
    })
