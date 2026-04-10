
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",include("BookApp.urls")),
    path("accounts/", include("accounts.urls")),
    path("books/", include("books.urls")),
    # path("transactions/", include("transactions.urls")),
]
