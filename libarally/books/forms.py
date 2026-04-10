from django import forms 
from .models import Book,Biblio,Shelf,Floor



class BaseForm(forms.ModelForm):
    class Meta:
        abstract = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
        

class BookForm(BaseForm):
    class Meta:
        model = Book
        fields = ["biblio","shelf",]


class BiblioForm(BaseForm):
    class Meta:
        model = Biblio
        fields = ["isbn", "title", "author","publisher",]

class ShelfForm(BaseForm):
    class Meta:
        model =Shelf
        fields = ["name", "floor"]
    
class FllorForm(BaseForm):
    class Meta:
        model = Floor
        fields = ["name"]


