# billing/forms.py
from django import forms
from .models import Billing, AccountantProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Insurance
# from doctor.models import Clinic
# Form for the User account (login details)
class AccountantUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        
class BillingForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = [
            'doctor', 'clinic', 'billing_type', 'content_type', 'object_id',
            'total_amount', 'payment_method', 'paid_by','patient'
        ]


# Form for the Accountant Profile details
class AccountantProfileForm(forms.ModelForm):
    # Make the clinic a dropdown of existing clinics
    # clinic = forms.ModelChoiceField(queryset=Clinic.objects.all(), empty_label="-- Select a Clinic --")
    
    class Meta:
        model = AccountantProfile
        # Use the fields from your new model
        fields = [
            'phone',
            'email',
            'address',
            'department',
            'profile_pic'
        ]

class BillUpdateForm(forms.ModelForm):
    # We define the insurance_claim field here to control its queryset
    insurance_claim = forms.ModelChoiceField(
        queryset=Insurance.objects.none(), # Start with an empty queryset
        required=False # It's not always required
    )

    class Meta:
        model = Billing
        # These are the fields the accountant can edit
        fields = ['paid_by', 'insurance_claim', 'payment_method', 'paid']
        widgets = {
            'paid_by': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # This is the magic part that filters the dropdown
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If the form is for an existing bill (instance is passed)
        if self.instance and self.instance.pk:
            # Filter the insurance_claim dropdown to only show approved policies for this bill's patient
            patient_user = self.instance.patient
            self.fields['insurance_claim'].queryset = Insurance.objects.filter(
                patient__patient=patient_user, 
            )