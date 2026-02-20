from django.urls import path
from.views import BookListView

app_name = "BookApp"

urlpatterns = [
    path("list/", BookListView.as_view(), name="BookList")
]




