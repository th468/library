from django.urls import path
from . import views

app_name = "accounts"


urlpatterns = [
    path("regist/", views.regist, name="regist"),
    
    
]

