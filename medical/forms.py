
from django import forms
from medical.models import Medicine

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MedicalProfile

# This form handles the User model fields (username, password, etc.)
class MedicalUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']


# This form handles the MedicalProfile model fields
class MedicalProfileForm(forms.ModelForm):
    class Meta:
        model = MedicalProfile
        fields = [
            'pharmacy_name',
            'phone',
            'email',        # Included as you requested
            'address',
            'profile_pic',
        ]

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            'name', 
            'brand', 
            'strength', 
            'price_per_unit', 
            'stock_quantity'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Paracetamol'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Crocin'}),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }