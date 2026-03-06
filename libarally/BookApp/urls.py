from django.urls import path
from . import views

app_name = "BookApp"

urlpatterns = [
    # path("list/", BookListView.as_view(), name="BookList")
    path("",views.index, name="index"),
]




