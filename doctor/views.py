from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .forms import DoctorRegisterForm, DoctorProfileForm
from django.contrib.auth.decorators import login_required
from .models import DoctorProfile
# from django.views import View
from .models import DoctorProfile,PatientDocConfig
from patient.models import PatientProfile,PatientVitals,LabReports,Records
import datetime
from django.db.models import Q
from centralapp.api_client import store_doctor_profile, get_user_profile,store_lab_report,get_lab_reports

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
    pats = PatientDocConfig.objects.filter(doctor_id=request.user.id)
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
    
    
    
    
    # pats = PatientDocConfig.objects.filter(doctor_id=request.user.id)
    # print(len(pats))

    # patient_l = []
    # for p in pats:
    #     print("hello")
    #     # Filter the patient profile using access code
    #     patient_profiles = PatientProfile.objects.filter(access_code=p.access_code)
    #     if patient_profiles.exists():
    #         patient_l.append(patient_profiles[0]),
    #     else:
    #         print(f"No patient profile found for access code: {p.access_code}")

    # print(len(patient_l))

    # return render(request, 'doctor/patientList.html', {'patientl': patient_l})
    
    # pats=PatientDocConfig.objects.filter(doctor_id=request.user.id)
    # print(len(pats))

    # patient_l=[]
    # for p in pats:
    #     print("hello")
    #     patient_l.append(PatientProfile.objects.filter(access_code=p.access_code)[0])

    # Patient_list=PatientProfile.objects.filter()
    # print(len(patient_l))


    # return render(request, 'doctor/patientList.html',{'patientl':patient_l})


@login_required
def pat_profile(request, p):
    subject = PatientProfile.objects.filter(id=p)[0]
    pat_user = User.objects.get(id=subject.userid)
    
    get_user_profile(subject.access_code)
    get_lab_reports(subject.access_code)
    
    pat_vitals = PatientVitals.objects.filter(patientv=pat_user)
    all_reports = Records.objects.filter(patient_id=p).order_by('id').reverse()
    all_lab = LabReports.objects.filter(patientl=pat_user).order_by('id').reverse()
    
    for report in all_reports:
        des = report.medication
        med = des.split(":")
        m_list = [] 
        for m in med:
            dosage = m.split("/")
            m_list.append(dosage)
        report.medication = m_list
        
    context = {
        'subject': subject,
        'vitals': pat_vitals.first(),
        'Reports': all_reports,
        'labreports': all_lab,
    }
    
    return render(request, 'doctor/patient_records_in_doc.html', context)

@login_required
def newReport(request,p):
    doctor=DoctorProfile.objects.filter(doctor=request.user)[0]
    patient=PatientProfile.objects.filter(id=p)[0]
    date=str(datetime.datetime.now()).split(" ")[0]

    obj={'doctor_name':doctor.name,'patient_name':patient.name,'date':date,"docid":doctor.id,"patid":patient.id}
    return render(request,'doctor/report.html',{'details':obj})

@login_required
def addReport(request):
    if request.method=="POST":
        new_record=Records()
        new_record.date=str(datetime.datetime.now()).split(" ")[0]
        new_record.diagnosis=request.POST['diagnosis']
        new_record.doctor_name=request.POST['doctor_name']
        new_record.Symptoms=request.POST['symptoms']
        new_record.medication=request.POST['medication']
        new_record.patient_id=request.POST['patid']
        new_record.doctor_id=request.POST['docid']
        new_record.additional_precautions=request.POST['additional_precautions']
        new_record.save()

        str_record = f"""Date: {new_record.date}
            Patient ID: {new_record.patient_id}
            Doctor ID: {new_record.doctor_id}
            Doctor Name: {new_record.doctor_name}
            Diagnosis: {new_record.diagnosis}
            Symptoms: {new_record.Symptoms}
            Medication: {new_record.medication}
            Additional Precautions: {new_record.additional_precautions}"""
        
        patient_accesscode=PatientProfile.objects.filter(id=str(request.POST["patid"]))[0].access_code

        report_data = {
            "reportData": str_record,
            "accessCode": patient_accesscode
        }
        store_lab_report(report_data)

        

        addr='doctor:pat_profile/'+ str(request.POST['patid'])

        return redirect('/pat_profile/'+ str(request.POST['patid']))

@login_required
def addPatient(request):
    print("entered1")
    
    accesscode=request.POST['accesscode']
    print(accesscode)
    print("entered")
    if len(PatientProfile.objects.filter(access_code=accesscode))==0:
        return redirect('/PatientList/')
    else:
        print("heya")
        check_pat=PatientProfile.objects.filter(access_code=accesscode)[0]
        print(check_pat.access_code)
        get_user_profile(accesscode)
           
        new_config=PatientDocConfig()
            
        new_config.doctor_id=request.user.id
        new_config.access_code=accesscode
        new_config.save()
        return redirect('/PatientList/')
        
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

# def profile_view(request):
#     return render(request, 'profile_view.html')
#     doctor = get_object_or_404(DoctorProfile, doctor=request.user)
#     # patient = PatientProfile.objects.get(patient=request.user)
#     # if request.method == 'POST':
#     form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
#     # if request.method == 'POST':

#     if form.is_valid():
#         doctor = form.save(commit=False)
#         doctor.doctor = request.user
#         doctor.save()
#         return redirect('doctor:doctorProfile')
#     # else:
#     #     form = PatientProfileForm()
#     return render(request,'doctor/doctor_profile_edit.html',{'form':form})

# @login_required
# class mypatients(View):
#     def get(self,request):
#         return render(request, 'doctor/temp.html',{})

def profile_view(request):
    return render(request, 'profile.html')

























# ========================================================================
# ========================================================================

#
# from .models import doc_details,patient_doc_config,records
# from django.contrib.sessions.models import Session
# from patient.models import patient_details
#
# # Create your views here.
# def doctor_profile(request):
#     return render(request,'doctor/doctor_profile.html')
#
# def doctorRecords(request):
#     return render(request, 'doctor/doctor_records.html')
#
# def registerpage(request):
#     return render(request,'doctor/register.html')
#
#
#
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
#
#         if len(username)>15:
#             messages.error(request,'length of username should be less than15')
#             return redirect('patient:registerpage')
#
#
#
#         myuser=User.objects.create_user(username,email,password)
#         myuser.first_name=fname
#         myuser.last_name=lname
#
#         new_doc=doc_details()
#         new_doc.lname=lname
#         new_doc.fname=fname
#         new_doc.username=username
#         new_doc.email=email
#         new_doc.save()
#
#         myuser.save()
#
#         newPatient=patient_doc_config()
#         newPatient.patient_username="sample_pusername"
#         newPatient.doctor_username=username
#         newPatient.auth_key=123
#         newPatient.save()
#
#         messages.success(request, 'Form submission successful')
#         return redirect('/')
#
#
#     else :
#         return HttpResponse('404-not found')
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
#             request.session["username_d"]=username
#             return render(request,'doctor/doctor_profile.html',{"username":username})
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
# def myPatients(request):
#     username=request.session["username_d"]
#     if len(patient_doc_config.objects.filter(doctor_username=username))!=0:
#         pat=patient_doc_config.objects.filter(doctor_username=username)
#         return render(request, 'doctor/mypatients.html',{"patients":pat})
#
#     else :
#         return render(request, 'doctor/mypatients.html',{"patients":"add patients"})
#
#
#     return render(request, 'doctor/mypatients.html',{"username":username})
#
# def doctorProfile(request):
#     return render(request, 'doctor/doctor_profile.html')
#
# def addpatient(request):
#     if request.method=="POST":
#         p_username=request.POST['username']
#         accesscode=request.POST['accesscode']
#
#         if len(patient_details.objects.filter(username=p_username))!=0:
#             pat=patient_details.objects.get(username=p_username)
#             if  pat.auth_key==accesscode:
#
#                 newPatient=patient_doc_config()
#                 newPatient.patient_username=p_username
#                 newPatient.doctor_username=request.session["username_d"]
#                 newPatient.auth_key=accesscode
#                 newPatient.save()
#                 redirect('doctor:myPatients')
#             else :
#                 redirect('doctor:myPatients')
#                 messages.error(request,'access code did not match')
#         else:
#              redirect('doctor:myPatients')
#              messages.error(request,'username does not exist')
#
#
#
#
#         return redirect('doctor:myPatients')
#
#
#     else:
#          return HttpResponse('404-not found')
#
# def doctorRecords(request,p_username):
#     request.session["username_p"]=p_username
#     return render(request, 'doctor/doctor_records.html')
#
#
#
# def addRecord(request):
#     return render(request,'doctor/report.html')
#
# def newReport(request):
#     diagnosis=request.POST['diagnosis']
#     doctor_notes=request.POST['doctor_notes']
#     medications=request.POST['medications']
#
#     new_record=records()
#     new_record.diagnosis=diagnosis
#     new_record.doctor_notes=doctor_notes
#     new_record.medications=medications
#     new_record.doctor_username=request.session["username_d"]
#     new_record.patient_username=request.session["username_p"]
#     new_record.save()
#
#     return redirect('doctor:doctorRecords', p_username=request.session["username_p"])
#
