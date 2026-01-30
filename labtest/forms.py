from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import LabStaffProfile, LabTest


# ----------------- LabStaff Registration ----------------- #
class LabStaffRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


# ----------------- LabStaff Profile ----------------- #
class LabStaffProfileForm(forms.ModelForm):
    class Meta:
        model = LabStaffProfile
        fields = [
            'full_name', 'phone', 'email', 'address',
            'qualification', 'gender', 'age', 'profile_picture'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ----------------- LabTest Form (Like Medicine Form) ----------------- #
class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        exclude = [
            'test_date', 'labstaff', 'clinic', 'billing',
            'finding', 'diagnosis', 'amount', 'report_file',
            'doctor', 'patient', 'status'  # ✅ exclude fields set in view
        ]
        widgets = {
            'test_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Blood Test'}),
        }

