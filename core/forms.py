from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Item, ItemImage, UserProfile

class ItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-black focus:outline-none"
            })


    class Meta:
        model = Item
        fields = ["title", "description", "category"]
        labels = {
            "title": "Megnevezés",
            "description": "Leírás",
            "category": "Kategória"
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ItemImageForm(forms.ModelForm):
    class Meta:
        model = ItemImage
        fields = ["image"]

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

class UserProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-black focus:outline-none"
            })

    class Meta:
        model = UserProfile
        fields = ["display_name", "phone", "address", "about", "avatar"]
        labels = {
            "display_name": "Megjelenített név",
            "phone": "Telefon",
            "address": "Lakcím",
            "about": "Bemutatkozás",
            "avatar": "Profilkép",
        }
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4}),
        }