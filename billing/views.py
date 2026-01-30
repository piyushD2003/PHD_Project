from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from billing.models import Billing
from billing.forms import BillingForm 
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from doctor.models import DoctorProfile
from doctor.models import Clinic
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import AccountantUserForm, AccountantProfileForm, BillUpdateForm # We will use the second form next
from django.contrib.auth.forms import UserCreationForm
import requests
from .models import AccountantProfile
from labtest.models import LabTest
from django.utils import timezone


# This is the registration view
def accountant_register(request):
    if request.method == 'POST':

        form = UserCreationForm(request.POST)
        print(form.is_valid(), form.is_valid)
        if form.is_valid():
            user = form.save()
            
            # 🔑 Automatically log the user in
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, "Accountant user registered successfully!")
                return redirect('billing:create_accountant_profile')
            else:
                messages.error(request, "Authentication failed. Please log in manually.")
                # return redirect('insurance:insurance_login')
    else:
        form = UserCreationForm()
    
    # We need a template named 'accountant_register.html'
    return render(request, 'billing/accountant_register.html', {'form': form})

@login_required
def create_accountant_profile(request):
    # Check if a profile already exists to prevent creating a second one
    if hasattr(request.user, 'accountant_profile'):
        return redirect('billing:view_accountant_profile') # Or wherever you want to send them

    if request.method == 'POST':
        form = AccountantProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user # Link the profile to the current user
            profile.clinic = Clinic.objects.first() 
            profile.save()

            profile_data = {
                "name": request.user.get_full_name(),
                "username": request.user.username,
                "department": profile.department,
                "phone": profile.phone,
                "email": profile.email,
                "address": profile.address
            }

            store_accountant_profile(profile_data)
            messages.success(request, 'Your profile has been created successfully.')
            # Redirect to the dashboard after profile creation
            return redirect('billing:view_accountant_profile') # We will create this dashboard soon
    else:
        form = AccountantProfileForm()
    
    # We need a template named 'create_accountant_profile.html'
    return render(request, 'billing/create_accountant_profile.html', {'form': form})

def store_accountant_profile(data):
    url = "http://127.0.0.1:8000/api/accountant/store"  
    try:
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            print("Warning: Received non-JSON response")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error sending insurance profile: {e}")
        return None

@login_required
def view_accountant_profile(request):
    # Safely get the profile for the logged-in user, or show a 404 error if it doesn't exist
    profile = get_object_or_404(AccountantProfile, user=request.user)
    is_accountant = hasattr(request.user, 'accountant_profile')
    context = {
        'profile': profile,
        'is_accountant': is_accountant
    }
    # This view will use a template named 'view_accountant_profile.html'
    return render(request, 'billing/view_accountant_profile.html', context)

@login_required
def process_unpaid_bills(request):
    # Start with the base query: all unpaid bills
    # .select_related() is a performance optimization to fetch related objects in one go
    bills_list = Billing.objects.filter(paid=False).select_related('patient', 'doctor').order_by('-date')

    # Get filter values from the URL (e.g., /.../?patient_name=John)
    patient_name = request.GET.get('patient_name', '')
    doctor_name = request.GET.get('doctor_name', '')
    billing_type = request.GET.get('billing_type', '')

    # Apply filters if they exist
    if patient_name:
        bills_list = bills_list.filter(patient__username__icontains=patient_name)
    
    if doctor_name:
        bills_list = bills_list.filter(doctor__name__icontains=doctor_name)
    
    if billing_type:
        bills_list = bills_list.filter(billing_type=billing_type)

    context = {
        'bills': bills_list,
        'billing_type_choices': Billing.BILLING_TYPE_CHOICES, # For the filter dropdown
        # Pass the current filter values back to the template to keep them in the search boxes
        'filter_values': {
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'billing_type': billing_type,
        }
    }
    # This view will use a template named 'process_unpaid_bills.html'
    return render(request, 'billing/process_unpaid_bills.html', context)

@login_required
def update_bill_view(request, pk):
    # Get the specific bill object, or show a 404 error if it doesn't exist
    bill = get_object_or_404(Billing, pk=pk)
    print("erytretreter",)
    if request.method == 'POST':
        # Pass the submitted data and the specific bill instance to the form
        form = BillUpdateForm(request.POST, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bill #{bill.id} has been updated successfully.')
            # Redirect back to the list of unpaid bills
            return redirect('billing:process_unpaid_bills')
    else:
        # On a GET request, create the form pre-filled with the bill's data
        form = BillUpdateForm(instance=bill)

    context = {
        'form': form,
        'bill': bill
    }
    # This view will use a template named 'update_bill.html'
    return render(request, 'billing/update_bill.html', context)

@login_required
def paid_bills_history(request):
    # The only change is here: filter(paid=True)
    bills_list = Billing.objects.filter(paid=True).select_related('patient', 'doctor').order_by('-date')

    # The filtering logic is identical
    patient_name = request.GET.get('patient_name', '')
    doctor_name = request.GET.get('doctor_name', '')
    billing_type = request.GET.get('billing_type', '')

    if patient_name:
        bills_list = bills_list.filter(patient__username__icontains=patient_name)
    
    if doctor_name:
        bills_list = bills_list.filter(doctor__name__icontains=doctor_name)
    
    if billing_type:
        bills_list = bills_list.filter(billing_type=billing_type)

    context = {
        'bills': bills_list,
        'billing_type_choices': Billing.BILLING_TYPE_CHOICES,
        'filter_values': {
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'billing_type': billing_type,
        }
    }
    # This will use a new template named 'paid_bills_history.html'
    return render(request, 'billing/paid_bills_history.html', context)


@login_required
def auto_generate_labtest_bill(labtest_id):
    lab_test = LabTest.objects.get(id=labtest_id)
    if not lab_test.billing:
        billing = Billing.objects.create(
            patient=lab_test.patient,
            doctor=lab_test.doctor,
            clinic=lab_test.clinic,
            test_name=lab_test.test_type,
            test_amount=lab_test.amount,
            date=timezone.now(),
            billing_type="Lab Test"
        )
        lab_test.billing = billing
        lab_test.save()

