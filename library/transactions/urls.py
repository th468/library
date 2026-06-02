from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('lend/<int:pk>/', views.LendActionView.as_view(), name='lend'),
    path('reserve/<int:pk>/', views.ReserveActionView.as_view(), name='reserve'),
    path("collect/<int:pk>/", views.CollectActionView.as_view(), name="collect"),
    path("renew/<int:pk>/", views.RenewActionView.as_view(), name="renew"),
    path("reserve/cancel/<int:pk>/", views.ReservationCancelActionView.as_view(), name="reserve_cancel"),
    ]

