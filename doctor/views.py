from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.db import transaction
from .forms import DoctorRegisterForm, DoctorProfileForm
from django.contrib.auth.decorators import login_required
from .models import DoctorProfile
# from django.views import View
from .models import DoctorProfile,PatientDocConfig
from patient.models import PatientProfile,PatientVitals,LabReports,Records
from medical.models import Medicine, Prescription, PrescriptionItem
import datetime
from django.db.models import Q
from centralapp.api_client import store_doctor_profile, get_user_profile,store_lab_report,get_lab_reports
from .models import Clinic
from .forms import ClinicForm
import requests
from labtest.forms import LabTestForm
from labtest.models import LabTest
from insurance.models import InsuranceProfile
from labtest.models import LabTest, LabStaffProfile
from billing.models import Billing
from medical.models import Prescription
from .forms import ClinicForm
from insurance.models import Insurance
from billing.models import Billing
from.forms import ClinicForm
from django.contrib.auth.forms import AuthenticationForm

def doctorRegister(request):
    if request.method =='POST':
        form = DoctorRegisterForm(request.POST)
        if form.is_valid():
            # form.save()
            # username = form.cleaned_data.get('username')
            # email = form.cleaned_data.get('email')
            # return redirect('login')
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            usertype = 2
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                return redirect('doctor:create_doctorprofile')
    else:
        form = DoctorRegisterForm()
    return render(request,'doctor/doctorRegister.html',{'form':form})

@login_required
def create_doctorprofile(request):
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.doctor = request.user
            doctor.save()

            # Store doctor profile in the API
            doctor_data = {
                "name": f"{doctor.doctor.first_name} {doctor.doctor.last_name}",
                "username": doctor.doctor.username,
                "specialization": doctor.Specialisation,
                "city": doctor.City,
                "college": doctor.College,
                "degree": doctor.Degree,
                "currentPlaceOfWork": doctor.Current_place_of_work,
                "yearOfCompletion": doctor.Year_of_completion,
                "registrationNumber": doctor.Registration_Number,
                "registrationCouncil": doctor.Registration_Council,
                "registrationYear": doctor.Registration_year,
                "contactNumber": doctor.phone,
                "aadharNumber": doctor.Aadhar_Number,
                "gender": doctor.Gender
            }
            store_doctor_profile(doctor_data)
             
            return redirect('doctor:doctorprofile')
    else:
        form = DoctorProfileForm()
    return render(request, 'doctor/doctor-profile-create.html', {'form': form})

def store_doctor_profile(data):
    url = "http://127.0.0.1:8000/api/doctor/store"  # Replace with your actual endpoint
    try:
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        try:
            return response.json()  # Try to decode JSON
        except ValueError:
            # JSONDecodeError (response was not valid JSON)
            print("Warning: Received non-JSON response")
            return None
    except requests.exceptions.RequestException as e:
        # Handles ConnectionError, Timeout, etc.
        print(f"Error sending doctor profile: {e}")
        return None

@login_required
def doctorprofile(request):
    profile=DoctorProfile.objects.filter(doctor=request.user).first()
    return render(request,'doctor/doctor_profile.html',{'profile':profile})
    # if request.method == 'POST':
    #     form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
    #     if form.is_valid():
    #         form.save()
    #         return redirect('doctor:doctorProfile')
    # else:
    #     form = DoctorProfileForm(instance=doctor)
    # return render(request, 'doctor/doctor_profile_edit.html', {'form': form})



@login_required
def PatientList(request):
    pats = PatientDocConfig.objects.all()
    print(len(pats))

    patient_l = []
    for p in pats:
        print("hello")
        # Filter the patient profile using access code that starts with digits 0-9
        patient_profiles = PatientProfile.objects.filter(
            Q(access_code__regex=r'^[0-9]')
        ).filter(access_code=p.access_code)
        
        if patient_profiles.exists():
            patient_l.append(patient_profiles[0])
        else:
            print(f"No patient profile found for access code: {p.access_code}")
    print(len(patient_l))

    return render(request, 'doctor/patientList.html', {'patientl': patient_l})


@login_required
def pat_profile(request, p):
    subject = PatientProfile.objects.filter(id=p)[0]
    pat_user = User.objects.get(id=subject.userid)
    
    get_user_profile(subject.access_code)
    # get_lab_reports(subject.access_code)
    
    pat_vitals = PatientVitals.objects.filter(patientv=pat_user)
    all_reports = Records.objects.filter(patient_id=p).order_by('id').reverse()
    all_lab = LabReports.objects.filter(patientl=pat_user).order_by('id').reverse()
    pending_labtests = LabTest.objects.filter(patient=subject, status='Pending')
    approved_labtests = LabTest.objects.filter(patient=subject, status='Approved')

    
    # for report in all_reports:
    #     des = report.medication
    #     med = des.split(":")
    #     m_list = [] 
    #     for m in med:
    #         dosage = m.split("/")
    #         m_list.append(dosage)
    #     report.medication = m_list
        
    context = {
        'subject': subject,
        'vitals': pat_vitals.first(),
        'Reports': all_reports,
        'labreports': all_lab,
        'labtests': pending_labtests,
        'approved_labtests': approved_labtests,

    }
    
    return render(request, 'doctor/patient_records_in_doc.html', context)

@login_required
def newReport(request,p):
    doctor = DoctorProfile.objects.filter(doctor=request.user)[0]
    patient = PatientProfile.objects.filter(id=p)[0]
    date = str(datetime.datetime.now()).split(" ")[0]

    # --- NEW CODE ---
    # Fetch all medicines from the catalog to show in a dropdown
    all_medicines = Medicine.objects.all().order_by('name')
    # --- END NEW CODE ---

    obj = {
        'doctor_name': doctor.name,
        'patient_name': patient.name,
        'date': date,
        "docid": doctor.id,
        "patid": patient.id,
        # --- NEW CODE ---
        # Add the medicine list to the context data
        'medicines': all_medicines
        # --- END NEW CODE ---
    }
    return render(request,'doctor/report.html',{'details':obj})

@login_required
def view_labtest_detail_from_doctor(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)
    return render(request, 'doctor/labtest_detail_doctor.html', {'lab_test': lab_test})

@login_required

def addReport(request):
    if request.method == "POST":
        # Get the IDs from the hidden form fields
        patient_id = request.POST.get('patid')
        doctor_id = request.POST.get('docid')

        # Use a database transaction to ensure all or nothing is saved
        try:
            with transaction.atomic():
                # 1. Get the main Patient and Doctor profile objects
                patient = PatientProfile.objects.get(id=patient_id)
                doctor = DoctorProfile.objects.get(id=doctor_id)

                # 2. Create the main Prescription object (the "header")
                new_prescription = Prescription.objects.create(
                    patient=patient,
                    doctor=doctor
                )

                # 3. Get the lists of medicine data from the form
                medicine_ids = request.POST.getlist('medicine')
                quantities = request.POST.getlist('quantity')
                instructions_list = request.POST.getlist('instructions')

                # 4. Loop through the submitted medicines and create PrescriptionItem objects
                for i in range(len(medicine_ids)):
                    medicine_id = medicine_ids[i]
                    # Skip if the user didn't select a medicine for a row
                    if not medicine_id:
                        continue
                        
                    medicine_obj = Medicine.objects.get(id=medicine_id)
                    PrescriptionItem.objects.create(
                        prescription=new_prescription,
                        medicine=medicine_obj,
                        quantity=quantities[i],
                        instructions=instructions_list[i]
                    )

                # 5. Create the main Record object and link the new prescription to it
                str_record = Records.objects.create(
                    date=str(datetime.datetime.now()).split(" ")[0],
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    doctor_name=request.POST.get('doctor_name'),
                    diagnosis=request.POST.get('diagnosis'),
                    Symptoms=request.POST.get('symptoms'),
                    additional_precautions=request.POST.get('additional_precautions'),
                    prescription=new_prescription
                )
                patient_accesscode=PatientProfile.objects.filter(id=str(request.POST["patid"]))[0].access_code

                report_data = {
                    "reportData": str_record,
                    "accessCode": patient_accesscode
                }
                # store_lab_report(report_data)
                

                # Your existing blockchain/external API call can stay if needed
                # (You might want to update what data you send to it later)
                # store_lab_report(...)

                messages.success(request, 'New record and prescription added successfully!')
                return redirect('doctor:pat_profile', p=patient_id)

        except Exception as e:
            # If any error occurs, the transaction will be rolled back
            messages.error(request, f'An error occurred: {e}')
            # Redirect back to the form page
            return redirect('doctor:newReport', p=patient_id)
    
    # If not a POST request, redirect to a safe page
    return redirect('doctor:doctorDashboard') # Change to your actual doctor dashboard URL


@login_required
def addPatient(request):
    if request.method == "POST":
        accesscode = request.POST.get('accesscode', '').strip()
        
        if not accesscode:
            messages.error(request, "Access code is required.")
            return redirect('doctor:PatientList')

        # Check if patient with the access code exists
        try:
            patient = PatientProfile.objects.get(access_code=accesscode)
        except PatientProfile.DoesNotExist:
            messages.error(request, "No patient found with that access code.")
            return redirect('doctor:PatientList')

        # Check for duplicate patient-doctor link
        if PatientDocConfig.objects.filter(doctor_id=request.user.id, access_code=accesscode).exists():
            messages.info(request, "This patient is already linked to you.")
            return redirect('doctor:PatientList')

        # Link the patient to the doctor
        PatientDocConfig.objects.create(
            doctor_id=request.user.id,
            access_code=accesscode
        )

        messages.success(request, "Patient successfully linked.")
        return redirect('doctor:PatientList')

    return redirect('doctor:PatientList')
        
@login_required
def editdoctorprofile(request):
    doctor = get_object_or_404(DoctorProfile, doctor=request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('doctor:doctorprofile')
    else:
        form = DoctorProfileForm(instance=doctor)
        
    return render(request, 'doctor/doctor_profile_edit.html', {'form': form})


def profile_view(request):
    return render(request, 'profile.html')
# ========================================================================
# ========================================================================

def clinic_login_view(request):
    if request.user.is_authenticated:
        return redirect('doctor:clinic_dashboard')  # ✅ Already handles logged-in users

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('doctor:clinic_dashboard')  # ✅ Redirects to dashboard
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()
    return render(request, 'doctor/clinic_login.html', {'form': form})

# --------------------------
# ✅ Clinic Logout View
# --------------------------
def clinic_logout_view(request):
    logout(request)
    return redirect('doctor:clinic_login')

# --------------------------
# ✅ Clinic Create View (only once)
# --------------------------
def create_clinic(request):
    if Clinic.objects.exists():
        messages.warning(request, "Clinic already exists.")
        return redirect('doctor:clinic_dashboard')

    if request.method == 'POST':
        form = ClinicForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Clinic created successfully.")
            return redirect('doctor:clinic_dashboard')
    else:
        form = ClinicForm()

    return render(request, 'doctor/clinic_form.html', {'form': form})

# --------------------------
# ✅ Clinic Dashboard View
# --------------------------
@login_required
def clinic_dashboard(request):
    clinic = Clinic.objects.first()
    doctors = DoctorProfile.objects.all()
    patients = PatientProfile.objects.all()
    insurances = InsuranceProfile.objects.all()
    labstaffs = LabStaffProfile.objects.all()
    labtests = LabTest.objects.all()
    prescriptions = Prescription.objects.all()
    billings = Billing.objects.all()
    context = {
        'clinic': clinic,
        'doctors': doctors,
        'patients': patients,
        'insurances': insurances,
        'labstaffs': labstaffs,
        'labtests': labtests,
        'prescriptions': prescriptions,
        'billings': billings,
    }

    return render(request, 'doctor/clinic_dashboard.html', context)
 
def doctor_list(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'doctor/doctor_list.html', {'doctors': doctors})

def view_all_insurances(request):
    insurances = Insurance.objects.all()
    return render(request, 'doctor/insurance_list.html', {'insurances': insurances})


def view_all_labtests(request):
    labtests = LabTest.objects.all()
    return render(request, 'doctor/labtest_list.html', {'labtests': labtests})

def view_all_prescriptions(request):
    prescriptions = Prescription.objects.all()
    return render(request, 'doctor/prescription_list.html', {'prescriptions': prescriptions})


def view_all_billings(request):
    billings = Billing.objects.all()
    print(billings)
    return render(request, 'doctor/billing_list.html', {'billings': billings})

def view_all_medical(request):
    medical_records = Records.objects.all().order_by('-id')
    patient_map = {p.id: p.name for p in PatientProfile.objects.filter(id__in=[r.patient_id for r in medical_records])}
    doctor_map = {d.id: d.name for d in DoctorProfile.objects.filter(id__in=[r.doctor_id for r in medical_records])}

    # Attach names to each record
    for rec in medical_records:
        rec.patient_name = patient_map.get(rec.patient_id, "Unknown Patient")
        rec.doctor_name = doctor_map.get(rec.doctor_id, "Unknown Doctor")
    return render(request, 'doctor/medical_list.html', {'medical_records': medical_records})