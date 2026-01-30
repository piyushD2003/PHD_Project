
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Insurance
from .models import InsuranceProfile

# User registration form
class InsuranceRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# # Insurance company profile form
# class InsuranceProfileForm(forms.ModelForm):
#     class Meta:
#         model = InsuranceProfile
#         fields = ['company_name', 'contact_number', 'address']


# Insurance policy form

class InsuranceProfileForm(forms.ModelForm):
    class Meta:
        model = InsuranceProfile
        fields = ['company_name', 'phone', 'email', 'address', 'department', 'profile_pic']

# class InsuranceForm(forms.ModelForm):
#     class Meta:
#         model = Insurance
#         fields = [
#             'insurance_status',
#             'insurance_provider',
#             'policy_number',
#             'policy_type',
#             'valid_from',
#             'valid_to',
#             'coverage_amount',
#             'is_active',
#             'policy_document',
#         ]

#         widgets = {
#             'valid_from': forms.DateInput(attrs={'type': 'date'}),
#             'valid_to': forms.DateInput(attrs={'type': 'date'}),
#         }

#         labels = {
#             'insurance_status': 'Insurance Status',
#             'insurance_provider': 'Provider Name',
#             'policy_number': 'Policy Number',
#             'policy_type': 'Policy Type',
#             'valid_from': 'Valid From',
#             'valid_to': 'Valid To',
#             'coverage_amount': 'Coverage Amount (INR)',
#             'is_active': 'Is Active?',
#             'policy_document': 'Upload Policy Document',
#         }

#     def __init__(self, *args, **kwargs):
#         super(InsuranceForm, self).__init__(*args, **kwargs)
#         for field in self.fields.values():
#             field.widget.attrs.update({'class': 'form-control'})
#         self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
    
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise forms.ValidationError("Email is already in use.")
#         return email
