from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Insurance
# from .forms import InsuranceForm
from doctor.models import Clinic
from patient.models import PatientProfile as Patient
from billing.models import Billing
from insurance.forms import InsuranceRegisterForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .forms import InsuranceProfileForm
from insurance.models import InsuranceProfile
from django.contrib.auth.forms import UserCreationForm
import requests
from django.db import transaction
from billing.models import Billing

def insurance_register(request):
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
                messages.success(request, "Insurance user registered successfully!")
                return redirect('insurance:insurance_profile_create')
            else:
                messages.error(request, "Authentication failed. Please log in manually.")
                return redirect('insurance:insurance_login')
    else:
        form = UserCreationForm()
    return render(request, 'insurance/insurance_register.html', {'form': form})

def insurance_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            from insurance.models import InsuranceProfile
            if InsuranceProfile.objects.filter(user=user).exists():
                return redirect('insurance:view_profile')
            else:
                return redirect('insurance:insurance_profile_create')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'insurance/login.html')


def insurance_logout(request):
    logout(request)
    return redirect('insurance:insurance_login')

@login_required
def create_insurance_profile(request):
    if InsuranceProfile.objects.filter(user=request.user).exists():
        return redirect('insurance:view_profile')

    if request.method == 'POST':
        form = InsuranceProfileForm(request.POST, request.FILES)
        if form.is_valid():
            insurance = form.save(commit=False)
            insurance.user = request.user
            insurance.clinic = Clinic.objects.first() 
            insurance.save()

           
            insurance_data = {
                "name": request.user.get_full_name(),
                "username": request.user.username,
                "company": insurance.company_name,
                "department": insurance.department,
                "phone": insurance.phone,
                "email": insurance.email,
                "address": insurance.address
            }
            store_insurance_profile(insurance_data)

            messages.success(request, "Insurance profile created successfully.")
            return redirect('insurance:view_profile')
    else:
        form = InsuranceProfileForm()
    return render(request, 'insurance/insurance_profile_create.html', {'form': form})

def store_insurance_profile(data):
    url = "http://127.0.0.1:8000/api/insurance/store"  
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
def view_insurance_profile(request):
    profile = get_object_or_404(InsuranceProfile, user=request.user)
    return render(request, 'insurance/insurance_profile_view.html', {'profile': profile})

@login_required
def edit_insurance_profile(request):
    insurance = get_object_or_404(InsuranceProfile, user=request.user)
    if request.method == 'POST':
        form = InsuranceProfileForm(request.POST, request.FILES, instance=insurance)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('insurance:insurance_view_profile')
    else:
        form = InsuranceProfileForm(instance=insurance)
    return render(request, 'insurance/edit_insurance_profile.html', {'form': form})

@login_required
def insurance_dashboard_view(request):
    # Get all insurance policies with the status 'Pending'
    pending_claims = Insurance.objects.filter(insurance_status='Pending')

    context = {
        'pending_claims': pending_claims
    }
    return render(request, 'insurance/dashboard.html', context)

@login_required
def claim_detail_view(request, pk):
    # This view now handles both GET (displaying) and POST (updating)
    
    # Get the specific insurance claim object
    claim = get_object_or_404(Insurance, pk=pk)

    # --- THIS IS THE POST LOGIC (handles the form submission) ---
    if request.method == 'POST':
        try:
            with transaction.atomic():
                new_status = request.POST.get('status')
                if new_status in ['Approved', 'Rejected']:
                    claim.insurance_status = new_status
                    claim.save()
                    messages.success(request, f'Claim has been updated to "{new_status}".')

                    # If approved, run the bill linking logic
                    if new_status == 'Approved':
                        bills_to_link = Billing.objects.filter(
                            patient=claim.patient.patient,
                            paid=False,
                            insurance_claim__isnull=True
                        )
                        bills_to_link.update(
                            insurance_claim=claim,
                            paid_by='Insurance'
                        )
                        if bills_to_link.count() > 0:
                            messages.info(request, f'{bills_to_link.count()} bills were linked to this claim.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
        
        # Redirect back to the same page after processing
        return redirect('insurance:claim_detail', pk=pk)

    # --- THIS IS THE GET LOGIC (displays the page) ---
    # Fetch all bills that are linked to THIS claim
    associated_bills = Billing.objects.filter(
        patient=claim.patient.patient, # The User object from the patient profile
        paid=False,
        insurance_claim__isnull=True # Only show bills that are not yet assigned to any claim
    ).order_by('date')
    
    # Put everything into the context
    context = {
        'insurance': claim,
        'bills': associated_bills  # <-- THIS IS THE FIX. We are now sending the bills.
    }
    
    return render(request, 'insurance/claim_detail.html', context)

@login_required
def approved_claims_view(request):
    # Get all insurance policies with the status 'Approved'
    approved_claims = Insurance.objects.filter(insurance_status='Approved')

    context = {
        'approved_claims': approved_claims
    }
    return render(request, 'insurance/approved_claims.html', context)

@login_required
def rejected_claims_view(request):
    # Get all insurance policies with the status 'Rejected'
    rejected_claims = Insurance.objects.filter(insurance_status='Rejected')

    context = {
        'rejected_claims': rejected_claims
    }
    return render(request, 'insurance/rejected_claims.html', context)

@login_required
def update_claim_status(request, pk):
    # This view should only be accessed via a POST request for security
    if request.method == 'POST':
        # Use a transaction to ensure all database operations succeed or fail together
        try:
            with transaction.atomic():
                # Get the insurance claim object
                insurance_claim = get_object_or_404(Insurance, pk=pk)
                
                # Get the new status from the button that was clicked ('Approved' or 'Rejected')
                new_status = request.POST.get('status')

                # --- THIS IS THE NEW AUTOMATION LOGIC ---
                if new_status == 'Approved':
                    # Find all unpaid, unassigned bills for this patient
                    bills_to_link = Billing.objects.filter(
                        patient=insurance_claim.patient.patient, # The User object
                        paid=False,
                        insurance_claim__isnull=True # Important: only get unassigned bills
                    )
                    
                    # Link them all to this claim and set paid_by to 'Insurance'
                    bills_to_link.update(
                        insurance_claim=insurance_claim,
                        paid_by='Insurance'
                    )
                    messages.info(request, f'{bills_to_link.count()} bills were linked to this claim.')
                # --- END OF AUTOMATION LOGIC ---

                # Update the claim status
                insurance_claim.insurance_status = new_status
                insurance_claim.save()

                messages.success(request, f'Claim has been updated to "{new_status}".')

        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
        
        # Redirect back to the same detail page to see the changes
        return redirect('insurance:claim_detail', pk=pk)

    # If not a POST request, just go back to the dashboard
    return redirect('insurance:dashboard')

@login_required
def pay_bill_view(request, pk):
    # This view only works with POST requests for safety
    print(pk)
    if request.method == 'POST':
        # Get the bill object by its ID (pk)
        bill = get_object_or_404(Billing, pk=pk)
        insurance_pk = request.POST.get('insurance_pk')
        # Update the 'paid' status to True
        bill.paid = True
        bill.insurance_claim=get_object_or_404(Insurance, pk=insurance_pk)
        bill.save()
        
        messages.success(request, f'Bill #{bill.pk} has been marked as paid.')
        
        # Redirect back to the claim detail page it came from.
        # We need the claim's pk to do this.
        return redirect('insurance:claim_detail', pk=bill.insurance_claim.pk)
        
    # If a user tries to access this URL directly (not via the button), just send them away.
    return redirect('insurance:dashboard')
# @login_required
# def create_insurance(request, patient_id=None, doctor_id=None):
#     if request.method == 'POST':
#         form = InsuranceForm(request.POST, request.FILES)
#         if form.is_valid():
#             try:
#                 insurance = form.save(commit=False)

#                 # Assign doctor
#                 if doctor_id:
#                     doctor = get_object_or_404(DoctorProfile, id=doctor_id)
#                 elif request.user.groups.filter(name='Doctors').exists():
#                     doctor = DoctorProfile.objects.filter(doctor=request.user).first()
#                 else:
#                     doctor = None
#                 insurance.doctor = doctor

#                 # Assign patient
#                 if patient_id:
#                     patient = get_object_or_404(Patient, id=patient_id)
#                 else:
#                     patient = Patient.objects.filter(patient=request.user).first()

#                 if not patient:
#                     messages.warning(request, "Patient profile not found. Please create one.")
#                     return redirect('patient:create_patientprofile')

#                 insurance.patient = patient

#                 # Assign clinic
#                 clinic = Clinic.objects.first()
#                 if not clinic:
#                     messages.warning(request, "No clinic found. Please set up a clinic.")
#                     return render(request, 'insurance/create_insurance.html', {'form': form})
#                 insurance.clinic = clinic

#                 # Assign billing
#                 if not insurance.billing:
#                     billing = Billing.objects.filter(patient=patient.patient).last()
#                     if billing:
#                         insurance.billing = billing
#                     else:
#                         messages.warning(request, 'No billing record found. Please create one.')
#                         return render(request, 'insurance/create_insurance.html', {'form': form})

#                 insurance.save()
#                 messages.success(request, "Insurance record created successfully.")
#                 print("Redirecting to insurance detail with ID:", insurance.id)
#                 return redirect('insurance:insurance_detail', insurance_id=insurance.id)

#             except Exception as e:
#                 messages.error(request, f"An error occurred while saving the insurance: {e}")
#                 print(f"[Error] {e}")
#         else:
#             messages.error(request, 'Form submission failed. Please correct the errors below.')
#             print(form.errors)
#     else:
#         form = InsuranceForm()

#     return render(request, 'insurance/create_insurance.html', {
#         'form': form,
#         'form_title': 'Create Insurance Record'
#     })

# @login_required
# def view_insurances(request):
#     insurances = Insurance.objects.all().order_by('-created_at')
#     return render(request, 'insurance/insurance_list.html', {'insurances': insurances})


# @login_required
# def insurance_detail(request, insurance_id):
#     insurance = get_object_or_404(Insurance, id=insurance_id, patient__patient=request.user)
#     return render(request, 'insurance/insurance_detail.html', {'insurance': insurance})

# # @login_required
# # def edit_insurance(request, insurance_id):
# #     insurance = get_object_or_404(Insurance, id=insurance_id, patient__patient=request.user)
# #     if request.method == 'POST':
# #         form = InsuranceForm(request.POST, request.FILES, instance=insurance)
# #         if form.is_valid():
# #             form.save()
# #             messages.success(request, 'Insurance record updated successfully.')
# #             return redirect('insurance:view_insurances')
# #     else:
# #         form = InsuranceForm(instance=insurance)
# #     return render(request, 'insurance/edit_insurance.html', {'form': form})

# @login_required
# def delete_insurance(request, insurance_id):
#     insurance = get_object_or_404(Insurance, id=insurance_id, patient__patient=request.user)
#     if request.method == 'POST':
#         insurance.delete()
#         messages.success(request, 'Insurance record deleted.')
#         return redirect('insurance:view_insurances')
#     return render(request, 'insurance/confirm_delete.html', {'insurance': insurance})
