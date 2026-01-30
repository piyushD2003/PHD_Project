from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate,login
from .forms import PatientRegisterForm,PatientProfileForm,PatientVitalsForm
from django.contrib.auth.decorators import login_required
from .models import PatientProfile,PatientVitals,Records,LabReports
from centralapp.api_client import store_user_profile, store_lab_report
import pytesseract
from PIL import Image
import hashlib
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib import messages
from .forms import InsuranceForm
from labtest.models import LabTest

#
# def auth(str):
#     return(hash(str))

# def create_profile(request):
#     form = ProfileForm(request.POST or None)  #class created in forms.py
#     if form.is_valid():
#         form.save()
#         return redirect('centralapp:mainpage')
#     return render(request,'centralapp/profile-create.html',{'form':form})
#
def patientRegister(request):
    if request.method =='POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            # form.save()
            # username = form.cleaned_data.get('username')
            # email = form.cleaned_data.get('email')
            # return redirect('login')
            user = form.save(commit=False)
            user.usertype= 1
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            # email = form.cleaned_data['email']
            # user.AccessCode = hash(email)
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('patient:create_patientprofile')
    else:
        form = PatientRegisterForm()
    return render(request,'patient/patientregister.html',{'form':form})

# @login_required
# def patient_create(request):
#     form = PatientForm()
#     if request.method == 'POST':
#         form = PatientForm(request.POST, request.FILES)
#         if form.is_valid():
#             patient = form.save(commit=False)
#             patient.user = request.user
#             patient.save()
#             return redirect('patient-detail')
#     context = {'form':form}
#     template = 'userinfo/patients/patient-create.html'
#     return render(request, template, context)


@login_required
def create_patientprofile(request):
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if profile already exists
            existing_profile = PatientProfile.objects.filter(patient=request.user).first()
            if existing_profile:
                form = PatientProfileForm(request.POST, request.FILES, instance=existing_profile)
                patient = form.save()
            else:
                patient = form.save(commit=False)
                patient.patient = request.user
                patient.save()

            # Calculate access_code as before
            concatenated_string = str(patient.id) + patient.address
            hash_object = hashlib.sha256(concatenated_string.encode())
            hash_hex = hash_object.hexdigest()
            access_code_int = int(hash_hex, 16)
            access_code_str = str(access_code_int)[-9:]
            if access_code_str[0] == '0':
                access_code_str = '1' + access_code_str[1:]

            patient.access_code = access_code_str
            patient.userid = request.user.id
            patient.save()

            # Store user profile in the API
            user_data = {
                "name": f"{patient.patient.first_name} {patient.patient.last_name}",
                "username": patient.patient.username,
                "email": patient.patient.email,
                "contactNumber": patient.phone,
                "emergencyContact": patient.emergency_contact,
                "age": patient.age,
                "gender": patient.gender,
                "profession": patient.profession,
                "aadharNumber": patient.Aadhar_Number,
                "residentialAddress": patient.address,
                "accessCode": patient.access_code
            }
            store_user_profile(user_data)

            return redirect('patient:patientvitals_input')
    else:
        form = PatientProfileForm()
    return render(request, 'patient/patient-profile-create.html', {'form': form})
#     if request.method == 'POST':
#         form = PatientProfileForm(request.POST)
#         if form.is_valid():
#             patient = form.save(commit=False)
#             patient.patient = request.user
#             patient.save()

#             patient = PatientProfile.objects.filter(patient=request.user)[0]
#             concatenated_string = str(patient.id) + patient.address

#             # Create a hash using SHA-256
#             hash_object = hashlib.sha256(concatenated_string.encode())
#             hash_hex = hash_object.hexdigest()
#             access_code_int = int(hash_hex, 16)  # Convert hash to an integer

#             # Ensure the access code is exactly 9 digits
#             access_code_str = str(access_code_int)[-9:]  # Get the last 9 digits

#             patient.access_code = access_code_str
#             patient.userid = request.user.id
#             patient.save()

#             return redirect('patient:patientvitals_input')
#     else:
#         form = PatientProfileForm()
#     return render(request, 'patient/patient-profile-create.html', {'form': form})

# def create_patientprofile(request):
#     if request.method =='POST':
#         form = PatientProfileForm(request.POST)
#         if form.is_valid():

#             patient = form.save(commit=False)
#             # name = form.cleaned_data['name']
#             # patient.AccessCode = hash(name)
#             patient.patient = request.user
#             patient.save()
#             # form.patient = request.user
#             # form.save()
#             patient=PatientProfile.objects.filter(patient=request.user)[0]
#             print(patient.address)
#             print(hash(patient.address))
#             patient.access_code=hash( str(patient.id) +patient.address)
#             patient.userid=request.user.id ##changed
#             patient.save()
            
#             return redirect('patient:patientvitals_input')
#     else:
#         form = PatientProfileForm()
#     return render(request,'patient/patient-profile-create.html',{'form':form})

@login_required
def patientvitals_input(request):
    if request.method =='POST':
        form = PatientVitalsForm(request.POST)
        if form.is_valid():
            patientv = form.save(commit=False)
            patientv.patientv = request.user
            patientv.save()
            # form.save()
            return redirect('patient:patientProfile')
    else:
        form = PatientVitalsForm()
    return render(request,'patient/patientvital_info.html',{'form':form})

 
@login_required
def patientProfile(request):
    profile = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
    return render(request, 'patient/patient_profile.html',{'profile':profile})

@login_required
def patientRecords(request):
    try:
        vitals = PatientVitals.objects.get(patientv=request.user)
    except PatientVitals.DoesNotExist:
        vitals = None

    try:
        patient = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
        if not patient:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        return redirect('patient:create_patientprofile')

    all_reports = Records.objects.filter(patient_id=patient.id).order_by('-id')

    current_labreports = LabReports.objects.filter(patientl=request.user).order_by('-id')[:1]

    lab_tests = LabTest.objects.filter(patient=patient).order_by('-test_date')

    context = {
        'vitals': vitals,
        'Reports': all_reports,
        'lab_rec': current_labreports,
        'lab_tests': lab_tests,  
    }

    return render(request, 'patient/patient_records.html', context)


@login_required 
def labreports(request):
    all_lab=LabReports.objects.filter(patientl=request.user)
    print(request.user.id)

    return render(request, 'patient/labreports.html',{"reports":all_lab})


@login_required
def addLabReports(request):
    if request.method == "POST":
        try:
            new_report = LabReports()
            new_report.patientl = request.user
            new_report.report_name = request.POST['report_name']
            new_report.report_date = request.POST['report_date']
            new_report.labreportfile = request.FILES['file']
            new_report.save()

            extracted_text = extract_text_from_image(new_report.labreportfile)

            report_data = {
                "reportData": extracted_text,
                "accessCode": PatientProfile.objects.filter(patient=request.user).latest('id').access_code
            }
            store_lab_report(report_data)

            return redirect('patient:labreports')
        except MultiValueDictKeyError:
            messages.error(request, 'Please select a file')
            return redirect('patient:labreports')
    else:
        return redirect('patient:labreports')

def extract_text_from_image(image):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    extracted_text = pytesseract.image_to_string(Image.open(image))
    # Replace '.' and ',' with newline character '\n'
    extracted_text = extracted_text.replace('.', '\n').replace(',', '\n')
    return extracted_text


@login_required
def patient_labtests_view(request):
    try:
        # Get the profile for the currently logged-in patient
        patient_profile = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        return redirect('patient:create_patientprofile')  # redirect if no profile

    # Fetch all lab tests assigned to this patient
    lab_tests = LabTest.objects.filter(patient=patient_profile)

    context = {
        'lab_tests': lab_tests
    }
    return render(request, 'patient/patient_labtests.html', context)

@login_required
def patient_labtest_detail(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id, patient__patient=request.user)
    
    context = {
        'lab_test': lab_test
    }
    return render(request, 'patient/patient_labtest_detail.html', context)

@login_required
def medications(request):
    patient = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
    all_reports=Records.objects.filter(patient_id=patient.id).order_by('id').reverse()
    
    # print(len(all_reports.reverse()))
    # for report in all_reports:
    #     des=report.medication
    #     med=des.split(":")
    #     m_list=[]
    #     for m in med:
    #         dosage=m.split("/")
    #         m_list.append(dosage)

    #     report.medication=m_list
        

    return render(request, 'patient/medications.html',{'Reports':all_reports})

@login_required
# def editPatient(request):
def editPatient(request):
    patient = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()  # Simplified saving
            return redirect('patient:patientProfile')
    else:
        form = PatientProfileForm(instance=patient)
    
    context = {
        'form': form,
        'patient_name': patient.patient.get_full_name(),  # Assuming User model has get_full_name method
    }
    
    return render(request, 'patient/patient-profile-edit.html', context)

@login_required
def editPatientVitals(request):
    patientv = get_object_or_404(PatientVitals, patientv=request.user)
    error =""
    if request.method == 'POST':    
        
        form = PatientVitalsForm(request.POST, request.FILES, instance=patientv)
        if form.is_valid():
            form.save()  # Simplified saving
            return redirect('patient:patientRecords')
        else:
            error = "Fill all fields properly"
    else:
        form = PatientVitalsForm(instance=patientv)
    
    context = {
        'form': form,
        'patient_name': patientv.patientv.get_full_name(),
        'error':error  # Assuming User model has get_full_name method
    }
    
    return render(request, 'patient/patient-vitals-edit.html', context)

@login_required
def create_insurance_view(request):
    try:
        # Get the profile for the currently logged-in patient
        patient_profile = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
        print(patient_profile)
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        return redirect('patient:create_patientprofile') # Or wherever you want to send users without a profile

    if request.method == 'POST':
        form = InsuranceForm(request.POST, request.FILES)
        if form.is_valid():
            # Don't save to the database yet
            insurance = form.save(commit=False)
            print(insurance)
            # Set the patient to the current user's profile
            insurance.patient = patient_profile
            # insurance.
            # Now save the full object
            insurance.save()
            
            messages.success(request, 'Your insurance details have been submitted for review.')
            # NOTE: Change 'patient_dashboard' to your actual dashboard URL name
            return redirect('patient:patientProfile') 
    else:
        # On a GET request, show a blank form
        form = InsuranceForm()

    context = {
        'form': form
    }
    return render(request, 'patient/create_insurance.html', context)

@login_required
def my_insurance_view(request):
    try:
        # Get the profile for the currently logged-in patient
        patient_profile = PatientProfile.objects.filter(patient=request.user).order_by('-id').first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        # Redirect to the page where they create a profile
        return redirect('patient:create_patientprofile')

    # Get all insurance policies linked to this patient's profile
    insurance_policies = patient_profile.insurances.all()

    context = {
        'insurance_policies': insurance_policies
    }
    return render(request, 'patient/my_insurance.html', context)


#     patient = get_object_or_404(PatientProfile, patient=request.user)
#     # patient = PatientProfile.objects.get(patient=request.user)
#     # if request.method == 'POST':
#     form = PatientProfileForm(request.POST, request.FILES, instance=patient)
#     # if request.method == 'POST':

#     if form.is_valid():
#         patient = form.save(commit=False)
#         patient.patient = request.user
#         patient.save()
#         return redirect('patient:patientProfile')
#     # else:
#     #     form = PatientProfileForm()
#     return render(request,'patient/patient-profile-edit.html',{'form':form})

# @login_required
# def editPatientVitals(request):
#     patientv = get_object_or_404(PatientVitals, patientv=request.user)
#     # if request.method == 'POST':
#     form = PatientVitalsForm(request.POST, request.FILES, instance=patientv)
#     if form.is_valid():
#         patientv = form.save(commit=False)
#         patientv.patientv = request.user
#         patientv.save()
#         return redirect('patient:patientRecords')
#     # else:
#         # form = PatientVitalsForm()
#     return render(request,'patient/patient-vitals-edit.html',{'form':form})



#
# def logout_view(request):
#     logout(request)
#     return render(r'^logout/$', 'django.contrib.auth.views.logout',
#                           {'next_page': '/successfully_logged_out/'})
#





# ===============================================================
# =================================================================
# ============================================================================

# from django.shortcuts import render,redirect
# from django.http import HttpResponse
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate,login,logout
# from django.contrib import messages
# from django.middleware.csrf import get_token
# # from .forms import RegisterForm, ProfileForm
# # from .models import Profile
# from django.contrib.auth.decorators import login_required
#
#
# from .models import patient_details,notes
# import random
# import string
#
# def get_random_string(length):
#     # Random string with the combination of lower and upper case
#     letters = string.ascii_letters
#     result_str = ''.join(random.choice(letters) for i in range(length))
#     print("Random string is:", result_str)
#
#
# def patientProfile(request):
#     return render(request, 'patient/patient_profile.html')
# def patientRecords(request):
#     return render(request, 'patient/patient_records.html')
#
# def labreports(request):
#     return render(request, 'patient/labreports.html')
# def medications(request):
#     return render(request, 'patient/medications.html')
#
# def registerpage(request):
#     return render(request,'patient/register.html')
#
# def signup(request):
#     if request.method=="POST":
#         fname=request.POST['fname']
#         lname=request.POST['lname']
#
#         username=request.POST['username']
#         password=request.POST['password']
#         email=request.POST['email']
#
#
#         if len(username)>15:
#             messages.error(request,'length of username should be less than15')
#             return redirect('patient:registerpage')
#
#         myuser=User.objects.create_user(username,email,password)
#         myuser.first_name=fname
#         myuser.last_name=lname
#
#
#         myuser.save()
#         print("1")
#
#         patient=patient_details()
#         patient.fname=fname
#         patient.lname=lname
#         patient.username=username
#         patient.auth_key=get_random_string(8)
#         patient.email=email
#         patient.save()
#
#         print('2')
#         messages.success(request, 'Form submission successful')
#         return redirect('/')
#
#
#     else :
#         return HttpResponse('404-not found')
#
#
#
#
# def loginn(request):
#     if request.method=="POST":
#         username=request.POST['username']
#         password=request.POST['password']
#         user=authenticate(username=username,password=password)
#         if user is not None:
#             login(request,user)
#             print("innn")
#             request.session["username_p"]=username
#             return render(request,'patient/patient_profile.html')
#
#         else :
#             print("invalid credentials")
#             return render(request,'centralapp/mainpage.html')
#
#
#         return HttpResponse('login')
#
#
#
#     else:
#         return HttpResponse('404-not found')
#
# def logout(request):
#     if request.method=="POST":
#         logout(request)
#         return render(request,'patient/mainpage.html')
#     return HttpResponse('logout')
#
#
# def addnotes(request):
#     if request.user.is_authenticated:
#         user=request.user
#         description=request.POST['description']
#         username= user.username
#         if len(notes.objects.filter(username_p=username))!=0:
#             notes.objects.filter(username_p=username).delete()
#             new_note=notes()
#             new_note.username_p=username
#             new_note.description=description
#             new_note.save()
#         else:
#             new_note=notes()
#             new_note.username_p=username
#             new_note.description=description
#             new_note.save()
#
#
#         return redirect('patient:personalNotes')
#
# def personalNotes(request):
#     csrf_token = get_token(request)
#     csrf_token_html = '<input type="hidden" name="csrfmiddlewaretoken" value="{}" />'.format(csrf_token)
#     if request.user.is_authenticated:
#         user=request.user
#         if len(notes.objects.filter(username_p=user.username))==0:
#             new_note = notes()
#             new_note.username_puser.username
#             new_note.description = 'Add your notes here'
#             new_note.save()
#         note=notes.objects.get(username_p=user.username)
#         return render(request, 'patient/personalNotes.html',{"des":note.description})
#
# # def create_item(request):
# #     form = ItemForm(request.POST or None)  #class created in forms.py
# #     if form.is_valid():
# #         form.save()
# #         return redirect('food:mainpage')
# #     return render(request,'food/item-form.html',{'form':form})
