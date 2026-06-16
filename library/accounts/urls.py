from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("regist/", views.UserRegistrationView.as_view(), name="regist"),
    path("profile/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("password_change/", views.UserPasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", views.UserPasswordChangeDoneView.as_view(), name="password_change_done"),
]
