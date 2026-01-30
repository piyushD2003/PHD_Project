from django.urls import path
from . import views
# from .views import create_labtest_by_labstaff


app_name = 'labtest'

urlpatterns = [
    # LabStaff Authentication & Profile Management
    path('register/', views.labstaff_register, name='labstaff_register'),
    path('login/', views.labstaff_login, name='labstaff_login'),
    path('logout/', views.labstaff_logout, name='labstaff_logout'),

    path('profile/create/', views.create_labstaff_profile, name='create_labstaff_profile'),
    path('profile/', views.view_labstaff_profile, name='view_labstaff_profile'),
    path('profile/edit/', views.edit_labstaff_profile, name='edit_labstaff_profile'),
   

    # Dashboard & Lab Test Handling
    path('dashboard/', views.labtest_dashboard_view, name='labtest_dashboard'),
    path('test/<int:pk>/', views.LabTestDetailView.as_view(), name='labtest_detail'),
    # path('test/<int:test_id>/', views.lab_test_detail_view, name='labtest_detail'),
    

    # Approve / Reject
    path('tests/approved/', views.approved_labtests_view, name='approved_labtests'),
    path('tests/rejected/', views.rejected_labtests_view, name='rejected_labtests'),

    # Records (reusing dashboard for now)
    path('records/', views.labtest_dashboard_view, name='view_lab_tests'),
    path('doctor/add-labtest/<int:patient_id>/', views.doctor_add_labtest, name='doctor_add_labtest'),
    path('labtest/<int:test_id>/update/', views.labtest_update_view, name='update_labtest'),
    
    path('labtest/<int:test_id>/dispense/', views.dispense_labtest, name='dispense_labtest'),
    path('billing/history/', views.labtest_billing_history, name='labtest_billing_history'),


]
