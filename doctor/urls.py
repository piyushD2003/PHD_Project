from . import views
from django.urls import path
from django.contrib.auth import views as authentication_views

app_name = 'doctor'
urlpatterns = [
    
    path('profile/', views.doctorprofile, name='doctorprofile'),
    path('createDoctorProfile/',views.create_doctorprofile,name ='create_doctorprofile'),
    path('doctorRegister/',views.doctorRegister,name = 'doctorRegister'),
    path('PatientList/',views.PatientList,name = 'PatientList'),
    path('pat_profile/<int:p>', views.pat_profile,name = 'pat_profile'),
    path('newReport/<int:p>',views.newReport,name="newReport"),
    path('addReport/',views.addReport,name="addReport"),
    path('addPatient/',views.addPatient,name="addPatient"), 
    path('editdocprofile/',views.editdoctorprofile,name="editdoctorprofile"), 
    path('profile-view/', views.profile_view, name='profile_view'),
    path('clinic/create/', views.create_clinic, name='create_clinic'),
    path('clinic/login/', views.clinic_login_view, name='clinic_login'),

    path('clinic/dashboard/', views.clinic_dashboard, name='clinic_dashboard'),
    # path('clinic/list/', views.clinic_list, name='clinic_list'),
    path('labtest/<int:test_id>/detail/', views.view_labtest_detail_from_doctor, name='view_labtest_detail_from_doctor'),

    # views.py
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('patients/', views.PatientList, name='PatientList'),
    path('insurances/', views.view_all_insurances, name='view_all_insurances'),
    path('labtests/', views.view_all_labtests, name='view_all_labtests'),
    path('prescriptions/', views.view_all_prescriptions, name='view_all_prescriptions'),
    path('billings/', views.view_all_billings, name='view_all_billings'),
    path('medical/', views.view_all_medical, name='view_all_medical'),

    
    
    # path('logout/', authentication_views.LogoutView.as_view(template_name='centralapp/logout.html'), name='logout'),
    # path('mypatients',views.mypatients,name = "mypatients"),
    # path('editDoctor/',views.editDoctor,name = 'editDoctor'),
]

# =============================================================================================
# =============================================================================================


    #   path('registerpage/',views.registerpage,name ='registerpage'),
    #    path('signup/',views.signup, name ='signup'),
    #      path('logind/',views.loginn, name ='logind'),
    #       path('myPatients/', views.myPatients, name='myPatients'),
    #   #     path('doctorProfile/', views.doctorProfile, name='doctorProfile'),
    #       path('addpatient/', views.addpatient, name='addpatient'),
    #       path('doctorRecords/<str:p_username>', views.doctorRecords, name='doctorRecords'),
    #        path('addRecord/', views.addRecord, name='addRecord'),
    #         path('newReport/', views.newReport, name='newReport'),
    #
    #
    # path('doctorprofile/', views.doctor_profile, name='doctor_profile'),
    #
    #
    #
    # # path('doclogin/',views.doclogin,name ='doclogin'),
    # # path('docregister/',views.docregister,name ='docregister')
