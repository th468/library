from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    path("lend/<int:book_id>/",views.LendView.as_view(), name="lend"),
    path("collect/<int:pk>/",views.CollectView.as_view(), name="collect"),
    path("renew/<int:pk>/",views.RenewView.as_view(), name="renew"),
]