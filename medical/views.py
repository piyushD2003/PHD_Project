# In medical/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests # Make sure you have 'requests' installed (pip install requests)
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import DetailView
from django.utils.decorators import method_decorator
from django.db import transaction

# Import your new forms and models
from .forms import MedicalUserForm, MedicalProfileForm, MedicineForm
from .models import MedicalProfile, Prescription, Medicine
from doctor.models import Clinic
from billing.models import Billing 
from doctor.models import DoctorProfile

# This view is for Step 1: Creating the user account
def medical_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 🔑 Automatically log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Please complete your profile.')
                # This redirect will now work correctly
                return redirect('medical:create_medical_profile')
            else:
                messages.error(request, 'Authentication failed after registration. Please try logging in.')
                return redirect('medical:medical_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
        
    return render(request, 'medical/medical_register.html', {'form': form})

# This view is for Step 2: Creating the professional profile
@login_required
def create_medical_profile(request):
    # If profile already exists, redirect to dashboard
    # if hasattr(request.user, 'medical_profile'):
    print(request)
    if MedicalProfile.objects.filter(user=request.user).exists():
        return redirect('medical:view_medical_profile')

    if request.method == 'POST':
        form = MedicalProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.clinic = Clinic.objects.first()
            profile.save()
            profile_data = {
                "name": request.user.get_full_name(),
                "username": request.user.username,
                "pharmacy_name": profile.pharmacy_name,
                "phone": profile.phone,
                "email": profile.email,
                "address": profile.address
            }
            # Placeholder for your external API call
            store_medical_profile(profile_data)

            messages.success(request, 'Your profile has been created successfully.')
            return redirect('medical:view_medical_profile')
    else:
        form = MedicalProfileForm()
    return render(request, 'medical/create_medical_profile.html', {'form': form})

def store_medical_profile(data):
    url = "http://127.0.0.1:8000/api/medical/store"  
    try:
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            print("Warning: Received non-JSON response")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error sending medical profile: {e}")
        return None
    
# View for logging in
def medical_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            # Check if they have a medical profile before redirecting
            if hasattr(user, 'medical_profile'):
                return redirect('medical:view_medical_profile')
            else:
                # If they have a user account but no profile
                return redirect('medical:create_medical_profile')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'medical/login.html')

# View for logging out
def medical_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('medical:medical_login')

# The main dashboard for the medical staff
@login_required
def medical_dashboard(request):
    # This is where we will list pending prescriptions later
    pending_prescriptions = Prescription.objects.filter(status='Pending')
    context = {
        'pending_prescriptions': pending_prescriptions
    }
    return render(request, 'medical/dashboard.html', context)

# View to see your own profile
@login_required
def view_medical_profile(request):
    profile = get_object_or_404(MedicalProfile, user=request.user)
    return render(request, 'medical/view_medical_profile.html', {'profile': profile})

# View to edit your own profile
@login_required
def edit_medical_profile(request):
    profile = get_object_or_404(MedicalProfile, user=request.user)
    if request.method == 'POST':
        form = MedicalProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('medical:view_medical_profile')
    else:
        form = MedicalProfileForm(instance=profile)
    return render(request, 'medical/edit_medical_profile.html', {'form': form})

# Placeholder function for your external API call, similar to the insurance one
def store_medical_profile(profile):
    url = "http://127.0.0.1:8000/api/medical/store" # Example URL
    try:
        data = {
            "username": profile.user.username,
            "pharmacy_name": profile.pharmacy_name,
            "phone": profile.phone,
            "email": profile.email,
            "address": profile.address
        }
        # response = requests.post(url, json=data, timeout=5)
        # response.raise_for_status()
        print(f"Data to send to external API: {data}")
    except Exception as e:
        print(f"Error sending medical profile data: {e}")

@method_decorator(login_required, name='dispatch')
class PrescriptionDetailView(DetailView):
    model = Prescription
    template_name = 'medical/prescription_detail.html'
    context_object_name = 'prescription'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can pass the total cost directly to the template
        prescription = self.get_object()
        context['total_cost'] = prescription.get_total_cost()
        return context

@login_required
def dispense_prescription(request, pk):
    # This view only accepts POST requests
    if request.method == 'POST':
        # Use a transaction to ensure all database changes succeed or none do
        try:
            with transaction.atomic():
                # 1. Get the prescription object, or return a 404 error if not found
                prescription = get_object_or_404(Prescription, pk=pk)

                # 2. Check if the prescription is still pending to prevent double-billing
                if prescription.status != 'Pending':
                    messages.warning(request, 'This prescription has already been processed.')
                    return redirect('medical:prescription_detail', pk=pk)

                # 3. Create the Billing object
                Billing.objects.create(
                    patient=prescription.patient.patient, # Get the User from the PatientProfile
                    doctor=prescription.doctor,
                    clinic =Clinic.objects.first(),
                    billing_type='Medical',
                    total_amount=prescription.get_total_cost(),
                    source=prescription,  # This links the bill to the prescription
                    paid=False
                )

                # 4. Update the prescription status to 'Dispensed'
                prescription.status = 'Dispensed'
                prescription.save()

                messages.success(request, f'Prescription #{prescription.id} has been dispensed and a bill has been generated.')
                # 5. Redirect to the dashboard to see the updated list
                return redirect('medical:medical_dashboard')

        except Exception as e:
            # If any error occurs, show an error message
            messages.error(request, f'An error occurred: {e}')
            return redirect('medical:prescription_detail', pk=pk)

    # If the request is not POST, just redirect back
    return redirect('medical:prescription_detail', pk=pk)

@login_required
def prescription_history(request):
    
    try:
        doctor = DoctorProfile.objects.get(doctor=request.user)  
    except DoctorProfile.DoesNotExist:
        messages.error(request, "No DoctorProfile found for this user.")
        return redirect('medical:billing_history')

    prescriptions = Prescription.objects.filter(status='Dispensed', doctor=doctor)
    print(prescriptions)
    return render(request, 'medical/prescription_history.html', {'prescriptions': prescriptions})

@login_required
def medicine_list_view(request):
    medicines = Medicine.objects.all().order_by('name')
    return render(request, 'medical/medicine_list.html', {'medicines': medicines})

# View to CREATE a new medicine
@login_required
def medicine_create_view(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New medicine added to catalog successfully.')
            return redirect('medical:medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'medical/medicine_form.html', {'form': form, 'title': 'Add New Medicine'})

# View to UPDATE an existing medicine
@login_required
def medicine_update_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{medicine.name}" has been updated.')
            return redirect('medical:medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'medical/medicine_form.html', {'form': form, 'title': f'Edit {medicine.name}'})

# View to DELETE a medicine
@login_required
def medicine_delete_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        medicine_name = medicine.name
        medicine.delete()
        messages.success(request, f'"{medicine_name}" has been deleted from the catalog.')
        return redirect('medical:medicine_list')
    return render(request, 'medical/medicine_confirm_delete.html', {'medicine': medicine})

@login_required
def create_medicine(request, patient_id=None, doctor_id=None):pass
    # if request.method == 'POST':
    #     form = MedicineForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             medicine = form.save(commit=False)

    #             # Assign doctor
    #             if doctor_id:
    #                 doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    #             elif request.user.groups.filter(name='Doctors').exists():
    #                 doctor = DoctorProfile.objects.filter(doctor=request.user).first()
    #             else:
    #                 doctor = None
    #             medicine.doctor = doctor

    #             # Assign patient
    #             if patient_id:
    #                 patient = get_object_or_404(Patient, id=patient_id)
    #             else:
    #                 patient = Patient.objects.filter(patient=request.user).first()

    #             if not patient:
    #                 messages.warning(request, "Patient profile not found. Please create one.")
    #                 return redirect('patient:create_patientprofile')

    #             medicine.patient = patient

    #             # Assign clinic
    #             clinic = Clinic.objects.first()
    #             if not clinic:
    #                 messages.warning(request, "No clinic found. Please set up a clinic.")
    #                 return render(request, 'medical/create_medicine.html', {'form': form})
    #             medicine.clinic = clinic

    #             # Assign billing
    #             if not medicine.billing:
    #                 billing = Billing.objects.filter(patient=patient.patient).last()
    #                 if billing:
    #                     medicine.billing = billing
    #                 else:
    #                     messages.warning(request, 'No billing record found. Please create one.')
    #                     return render(request, 'medical/create_medicine.html', {'form': form})

    #             medicine.save()
    #             messages.success(request, "Medicine record created successfully.")
    #             return redirect('medical:medicine_detail', medicine_id=medicine.id)

    #         except Exception as e:
    #             messages.error(request, f"An error occurred while saving the medicine: {e}")
    #             print(f"[Error] {e}")
    #     else:
    #         messages.error(request, 'Form submission failed. Please correct the errors below.')
    #         print(form.errors)
    # else:
    #     form = MedicineForm()

    # return render(request, 'medical/create_medicine.html', {
    #     'form': form,
    #     'form_title': 'Create Medicine Record'
    # })


@login_required
def view_medicines(request):pass
    # medicines = Medicine.objects.filter(patient__patient=request.user).order_by('-created_at')
    # return render(request, 'medical/medicine_list.html', {'medicines': medicines})


@login_required
def medicine_detail(request, medicine_id):pass
    # medicine = get_object_or_404(Medicine, id=medicine_id, patient__patient=request.user)
    # return render(request, 'medical/medicine_detail.html', {'medicine': medicine})


@login_required
def edit_medicine(request, medicine_id):pass
    # medicine = get_object_or_404(Medicine, id=medicine_id, patient__patient=request.user)
    # if request.method == 'POST':
    #     form = MedicineForm(request.POST, instance=medicine)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'Medicine record updated successfully.')
    #         return redirect('medical:view_medicines')
    # else:
    #     form = MedicineForm(instance=medicine)
    # return render(request, 'medical/edit_medicine.html', {'form': form})


@login_required
def delete_medicine(request, medicine_id):pass
    # medicine = get_object_or_404(Medicine, id=medicine_id, patient__patient=request.user)
    # if request.method == 'POST':
    #     medicine.delete()
    #     messages.success(request, 'Medicine record deleted.')
    #     return redirect('medical:view_medicines')
    # return render(request, 'medical/confirm_delete.html', {'medicine': medicine})
@login_required
def billing_history_view(request):
    # Get only Medical-related billings and order them by the billing date
    medical_bills = Billing.objects.filter(
        billing_type='Medical'
    ).select_related('patient', 'doctor').order_by('-date') 
    print(medical_bills[0])
    print(medical_bills[0].patient)
    context = {
        'medical_bills': medical_bills,
    }
    return render(request, 'medical/billing_history.html', context)

@login_required
def edit_medical_profile(request):
    # Ensure the medical profile exists
    profile, created = MedicalProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = MedicalProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('medical:view_medical_profile')  # change this to your profile view name
    else:
        form = MedicalProfileForm(instance=profile)

    return render(request, 'medical/edit_medical.html', {'form': form})

# @method_decorator(login_required, name='dispatch')
# class PrescriptionDetailView(DetailView):
#     model = Prescription
#     template_name = 'medical/prescription_detail.html'
#     context_object_name = 'prescription'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         prescription = self.get_object()

#         # Pass total cost
#         context['total_cost'] = prescription.get_total_cost()

#         # Get billing if it exists
#         billing = Billing.objects.filter(source=prescription).first()
#         context['billing'] = billing

#         return context
