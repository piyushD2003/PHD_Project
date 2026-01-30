from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import auth
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from patient.models import PatientProfile
from doctor.models import DoctorProfile
from insurance.models import InsuranceProfile
from medical.models import MedicalProfile
from billing.models import AccountantProfile
import pandas as pd
from .models import Diseases
from django.contrib import messages
from .api_client import get_user_profile,get_user_profile_by_username,get_doctor_profile
from labtest.models import LabStaffProfile


# from patient.models import PatientProfile
# import requests
# from bs4 import BeautifulSoup



def mainpage(request):
    # page = request.get('')
    # soup = BeautifulSoup(page.text,'html.parser')
    # https://www.niams.nih.gov/health-topics/all-diseases
    # https://www.cdc.gov/diseasesconditions/index.html
    # https://www.pinehurstmedical.com/internalmedicine/internal-medicine-diseases-disorders-a-syndromes/
    # https://familydoctor.org/diseases-and-conditions/
    return render(request,'centralapp/mainpage.html')


def marathi_view(request):
    return render(request,'centralapp/marathi.html')


def login(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=auth.authenticate(username=username,password=password)
        print(user)
        if user is not None:
            auth.login(request, user)
            usert =3
            # if request.user.patient.usertype=="1":
            if PatientProfile.objects.filter(patient = request.user):
                isuser = PatientProfile.objects.filter(patient = request.user)
                usert = [int(each.usertype) for each in isuser][0]
            elif DoctorProfile.objects.filter(doctor=request.user):
                isuser = DoctorProfile.objects.filter(doctor=request.user)
                usert = [int(each.usertype) for each in isuser][0]
            elif InsuranceProfile.objects.filter(user = request.user):
                get_user_profile(username)
                return redirect('insurance:view_profile')
            elif MedicalProfile.objects.filter(user = request.user):
                get_user_profile(username)
                print(MedicalProfile.objects.filter(user = request.user))
                return redirect('medical:view_medical_profile')
            elif AccountantProfile.objects.filter(user = request.user):
                get_user_profile(username)
                print(AccountantProfile.objects.filter(user = request.user))
                return redirect('billing:view_accountant_profile')
            elif LabStaffProfile.objects.filter(user = request.user):
                get_user_profile(username)
                print(LabStaffProfile.objects.filter(user = request.user))
                return redirect('labtest:view_labstaff_profile')
            
            
            # usertype = [int(each.usertype) for each in isuser][0]
            # usertype = [int(each.usertype) for each in isuser]
            if usert==1:
                get_user_profile_by_username(username)
                # return render(request,'centralapp/temp.html',{'isuser':isuser,'usert':usert})
                return redirect('patient:patientProfile')
            elif usert==2:
                get_doctor_profile(username)
                return redirect('doctor:doctorprofile')
            # return render(request,'centralapp/temp.html', {'isuser':isuser,'usertype':usertype})
        # elif request.user.doctor.usertype=="2":
        else:
            messages.info(request,"Invalid Credentials!")
            return redirect('login')
    return render(request,'centralapp/login.html')

# uniquetogether



def About_us(request):
    return render(request,'centralapp/about_us.html')
def Cancer(request):
    return render(request,'centralapp/cancer.html')
def Covid_19(request):
    return render(request,'centralapp/Covid_19.html')
def Diabetes(request):
    return render(request,'centralapp/diabetes.html')
def FAQS(request):
    return render(request,'centralapp/faqs.html')
def Heart_disorder(request):
    return render(request,'centralapp/heart_disorder.html')
def doc_how_to_use(request):
    return render(request,'centralapp/how_to_use_Doctor.html')
def patients_how_to_use(request):
    return render(request,'centralapp/how_to_use_User.html')
def Hypertension(request):
    return render(request,'centralapp/hypertension.html')
def Inside_health_records(request):
    return render(request,'centralapp/inside_health_records.html')
def Aids(request):
    return render(request,'centralapp/aids.html')


def searchBar(request):
    query=request.POST['searchBar']

    try:
        dis=Diseases.objects.get(name__icontains=query)
        return render(request,'centralapp/search_result.html',{"disease":dis})

    except :
        messages.error(request, f"Sorry! '{query}' does not exist in our Health Conditions dataset")
        return redirect('/')
    
def logout_user(request):
    logout(request)
    return redirect("/")


