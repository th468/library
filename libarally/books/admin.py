from django.contrib import admin

from .models import Biblio, Book, Floor, Shelf

admin.site.register(Floor)
admin.site.register(Shelf)
admin.site.register(Biblio)
admin.site.register(Book)


