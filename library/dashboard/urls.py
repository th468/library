from django.urls import path

from .views import DashboardIndexView, LendingHistoryView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardIndexView.as_view(), name="index"),
    path("history/", LendingHistoryView.as_view(), name="history"),
]
