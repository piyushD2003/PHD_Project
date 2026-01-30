from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import DetailView
from django.utils.decorators import method_decorator
import requests

from .forms import LabStaffProfileForm, LabTestForm
from .models import LabStaffProfile, LabTest
from doctor.models import Clinic
from doctor.models import DoctorProfile
from patient.models import PatientProfile
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.files.uploadedfile import UploadedFile
from billing.models import Billing
from django.db import transaction


# -------------------- AUTH --------------------

def labstaff_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Registration successful. Please complete your profile.")
                return redirect('labtest:create_labstaff_profile')
            else:
                messages.error(request, "Registration succeeded, but login failed.")
                return redirect('labtest:labstaff_login')
    else:
        form = UserCreationForm()
    return render(request, 'labtest/labstaff_register.html', {'form': form})

@login_required
def create_labstaff_profile(request):
    if LabStaffProfile.objects.filter(user=request.user).exists():
        return redirect('labtest:view_labstaff_profile')

    if request.method == 'POST':
        form = LabStaffProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.clinic = Clinic.objects.first()
            profile.save()

            store_labstaff_profile({
                "username": request.user.username,
                "name": profile.full_name,
                "email": profile.email,
                "phone": profile.phone,
                "address": profile.address,
                "qualification": profile.qualification,
                "clinic": profile.clinic.name if profile.clinic else None
            })
            messages.success(request, "Profile created successfully.")
            return redirect('labtest:view_labstaff_profile')
    else:
        form = LabStaffProfileForm()
    return render(request, 'labtest/labstaff_profile_create.html', {'form': form})

def store_labstaff_profile(data):
    url = "http://127.0.0.1:8000/api/labstaff/store"
    try:
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None

def labstaff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            try:
                profile = LabStaffProfile.objects.get(user=user)
                return redirect('labtest:view_labstaff_profile')
            except LabStaffProfile.DoesNotExist:
                return redirect('labtest:create_labstaff_profile')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'labtest/labstaff_login.html')

def labstaff_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('labtest:labstaff_login')

@login_required
def view_labstaff_profile(request):
    profile = get_object_or_404(LabStaffProfile, user=request.user)
    return render(request, 'labtest/view_labstaff_profile.html', {'profile': profile})


@login_required
def edit_labstaff_profile(request):
    profile = get_object_or_404(LabStaffProfile, user=request.user)
    if request.method == 'POST':
        form = LabStaffProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('labtest:view_labstaff_profile')
    else:
        form = LabStaffProfileForm(instance=profile)
    return render(request, 'labtest/edit_labstaff_profile.html', {'form': form})


@login_required
def labtest_dashboard_view(request):
    pending_labtests = LabTest.objects.filter(status='Pending')
    return render(request, 'labtest/dashboard.html', {'pending_labtests': pending_labtests})

@method_decorator(login_required, name='dispatch')
class LabTestDetailView(DetailView):
    model = LabTest
    template_name = 'labtest/labtest_detail.html'
    context_object_name = 'test'

    def post(self, request, *args, **kwargs):
        test = self.get_object()

        # If clinic is not assigned, assign the default clinic
        if not test.clinic:
            try:
                default_clinic = Clinic.objects.first()
                if default_clinic:
                    test.clinic = default_clinic
            except Clinic.DoesNotExist:
                messages.error(request, "Default clinic does not exist.")
                return redirect('labtest:labtest_dashboard')

        # Update test fields
        findings = request.POST.get('findings')
        diagnosis = request.POST.get('diagnosis')
        amount = request.POST.get('amount')
        report_file = request.FILES.get('report_file')

        if findings and diagnosis and amount:
            test.findings = findings
            test.diagnosis = diagnosis
            test.amount = amount
            if report_file:
                test.report_file = report_file

        # Action: Approve or Reject
        action = request.POST.get('action')
        if action == 'approve':
            test.status = 'Approved'
            messages.success(request, "Lab test approved and saved.")
        elif action == 'reject':
            test.status = 'Rejected'
            messages.success(request, "Lab test rejected.")

        test.save()

        return HttpResponseRedirect(reverse('labtest:labtest_detail', kwargs={'pk': test.pk}))
    
@login_required
def doctor_add_labtest(request, patient_id):
    try:
        # Get the current doctor's profile (DoctorProfile is linked to User via 'doctor' field)
        doctor_profile = get_object_or_404(DoctorProfile, doctor=request.user)
    except Exception as e:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor:doctorprofile')  # or a fallback page

    # Get patient profile by ID
    patient_profile = get_object_or_404(PatientProfile, id=patient_id)

    if request.method == 'POST':
        form = LabTestForm(request.POST, request.FILES)
        if form.is_valid():
            labtest = form.save(commit=False)
            labtest.doctor = doctor_profile  
            labtest.patient = patient_profile 
            labtest.status = 'Pending' 
            labtest.clinic = doctor_profile.clinic  
            labtest.save()
            messages.success(request, "Lab Test added successfully.")
            return redirect('doctor:pat_profile', p=patient_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LabTestForm()

    return render(request, 'doctor/doctor_add_labtest.html', {
        'form': form,
        'form_title': 'Add Lab Test for Patient',
        'patient': patient_profile
    })

@login_required
def approved_labtests_view(request):
    approved_labtests = LabTest.objects.filter(status='Approved')
    return render(request, 'labtest/approved_tests.html', {'approved_labtests': approved_labtests})


@login_required
def rejected_labtests_view(request):
    # Get all lab tests with the status 'Rejected'
    rejected_labtests = LabTest.objects.filter(status='Rejected')

    context = {
        'rejected_labtests': rejected_labtests
    }
    return render(request, 'labtest/rejected_tests.html', context)


@login_required
def labtest_update_view(request, test_id):
    test = get_object_or_404(LabTest, id=test_id)

    if request.method == 'POST':
        form = LabTestForm(request.POST, request.FILES, instance=test)
        if form.is_valid():
            updated_test = form.save(commit=False)
            updated_test.status = 'Approved'  
            updated_test.save()

           

            messages.success(request, "Lab test updated and approved.")
            return redirect('labtest:labtest_dashboard')
    else:
        form = LabTestForm(instance=test)

    return render(request, 'labtest/update_labtest.html', {
        'form': form,
        'test': test,
        'form_title': 'Update Lab Test'
    })

@login_required
def dispense_labtest(request, test_id):
    # Only accept POST requests
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Get the lab test object or return 404 if not found
                test = get_object_or_404(LabTest, pk=test_id)
                print("labtest222222222222222222222222222222222222")
                # 2. Ensure the lab test is approved (to avoid duplicate billing)
                if test.status != 'Approved':
                    messages.warning(request, 'Only approved lab tests can be billed.')
                    return redirect('labtest:labtest_detail', pk=test_id)
                print("labtest222222222222222222222222222222222222")

                # 3. Check if billing already exists for this lab test
                # print("hhj",Billing.objects.filter(source=test).exists())
                # if Billing.objects.filter(source=test).exists():
                #     messages.info(request, 'Billing for this lab test already exists.')
                #     return redirect('labtest:labtest_detail', pk=test_id)
                # print("labtest222222222222222222222222222222222222")

                # 4. Create a Billing entry
                a=Billing.objects.create(
                    patient=test.patient.patient,  # User from PatientProfile
                    doctor=test.doctor,
                    clinic=Clinic.objects.first(),  # Default clinic
                    billing_type='Lab Test',
                    total_amount=test.amount,
                    source=test,  # Link billing to this lab test
                    paid=False
                )
                print("labtest222222222222222222222222222222222222")

                print(a)

                # 5. Update lab test status to "Dispensed"
                test.status = 'Dispensed'
                test.save()

                # 6. Success message and redirect to dashboard
                messages.success(request, f'Lab Test #{test.id} has been dispensed and a bill has been generated.')
                return redirect('labtest:labtest_dashboard')

        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('labtest:labtest_detail', pk=test_id)

    # If not POST, redirect back to detail
    return redirect('labtest:labtest_detail', pk=test_id)



@login_required
def labtest_billing_history(request):
    labtest_bills = Billing.objects.filter(
        billing_type='Lab Test'
    ).select_related('patient', 'doctor').order_by('-date')

    return render(request, 'labtest/billing_history.html', {'labtest_bills': labtest_bills})