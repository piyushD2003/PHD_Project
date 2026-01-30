from django import forms
from django.core.exceptions import ValidationError
from .models import (
    OrganDonation, OrganRequest, OrganType, 
    BloodType, DoctorApproval, OrganTransaction
)


class OrganDonationForm(forms.ModelForm):
    """Form for registering organ donations"""
    
    class Meta:
        model = OrganDonation
        fields = ['organ_type', 'blood_type', 'health_condition', 'age_at_donation', 'available_from', 'notes']
        widgets = {
            'organ_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'blood_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'health_condition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your current health condition and any medical history...'
            }),
            'age_at_donation': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '18',
                'placeholder': 'Enter your age'
            }),
            'available_from': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional medical notes (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        age = cleaned_data.get('age_at_donation')
        
        if age and age < 18:
            raise ValidationError("You must be at least 18 years old to donate an organ.")
        
        organ_type = cleaned_data.get('organ_type')
        if not organ_type:
            raise ValidationError("Please select an organ type.")
        
        return cleaned_data


class OrganRequestForm(forms.ModelForm):
    """Form for requesting organs"""
    
    class Meta:
        model = OrganRequest
        fields = ['organ_type', 'blood_type', 'medical_condition', 'age_at_request', 'urgency', 'needed_by', 'notes']
        widgets = {
            'organ_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'blood_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'medical_condition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your medical condition and why you need this organ...'
            }),
            'age_at_request': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '0',
                'placeholder': 'Enter your age'
            }),
            'urgency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'needed_by': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional medical notes (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        age = cleaned_data.get('age_at_request')
        
        if age and age < 0:
            raise ValidationError("Age cannot be negative.")
        
        organ_type = cleaned_data.get('organ_type')
        if not organ_type:
            raise ValidationError("Please select an organ type.")
        
        return cleaned_data


class OrganMatchingForm(forms.Form):
    """Form for matching organ donations with requests"""
    
    donation = forms.ModelChoiceField(
        queryset=OrganDonation.objects.filter(status='available'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Select Organ Donation',
        required=True
    )
    
    request = forms.ModelChoiceField(
        queryset=OrganRequest.objects.filter(status='pending'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Select Organ Request',
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        donation = cleaned_data.get('donation')
        request = cleaned_data.get('request')
        
        if donation and request:
            # Check if organ types match
            if donation.organ_type != request.organ_type:
                raise ValidationError("Organ types must match to create a match.")
            
            # Check if donation is already matched
            if donation.status != 'available':
                raise ValidationError("This donation is not available for matching.")
            
            # Check if request is still pending
            if request.status != 'pending':
                raise ValidationError("This request is not pending.")
            
            # Check if donor and requester are different
            if donation.donor == request.requester:
                raise ValidationError("A donor cannot request their own donated organ.")
        
        return cleaned_data


class DoctorApprovalForm(forms.ModelForm):
    """Form for doctor approval of organ matches"""
    
    class Meta:
        model = DoctorApproval
        fields = ['status', 'reason']
        widgets = {
            'status': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide detailed reason for your decision...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        reason = cleaned_data.get('reason')
        
        if not reason or len(reason.strip()) == 0:
            raise ValidationError("Please provide a reason for your decision.")
        
        return cleaned_data


class OrganTransactionForm(forms.ModelForm):
    """Form for creating and managing organ transactions"""
    
    class Meta:
        model = OrganTransaction
        fields = ['notes', 'success_rate']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Transaction notes and outcomes...'
            }),
            'success_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '0',
                'max': '100',
                'step': '0.1',
                'placeholder': 'Enter success rate percentage (0-100)'
            }),
        }


class FilterOrganDonationForm(forms.Form):
    """Form for filtering organ donations"""
    
    organ_type = forms.ModelChoiceField(
        queryset=OrganType.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False,
        empty_label='All Organs'
    )
    
    blood_type = forms.ModelChoiceField(
        queryset=BloodType.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False,
        empty_label='All Blood Types'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(OrganDonation._meta.get_field('status').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )


class FilterOrganRequestForm(forms.Form):
    """Form for filtering organ requests"""
    
    organ_type = forms.ModelChoiceField(
        queryset=OrganType.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False,
        empty_label='All Organs'
    )
    
    blood_type = forms.ModelChoiceField(
        queryset=BloodType.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False,
        empty_label='All Blood Types'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(OrganRequest._meta.get_field('status').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )
    
    urgency = forms.ChoiceField(
        choices=[('', 'All Urgency Levels')] + list(OrganRequest._meta.get_field('urgency').choices),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )
