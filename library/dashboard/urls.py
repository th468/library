from django.urls import path

from .views import DashboardIndexView, LendingHistoryView,LendingListView,ReservationListView,FavoriteListView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardIndexView.as_view(), name="index"),
    path("history/", LendingHistoryView.as_view(), name="history"),
    path("lendings/", LendingListView.as_view(), name="lending_list"),
    path("reservations/", ReservationListView.as_view(), name="reservation_list"),
    path("favorites/", FavoriteListView.as_view(), name="favorite_list"),
]
