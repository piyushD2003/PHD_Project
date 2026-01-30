# medical/urls.py
from django.urls import path
from . import views
from .views import billing_history_view 

app_name = 'medical'

urlpatterns = [
    path('register/', views.medical_register, name='medical_register'),
    path('login/', views.medical_login, name='medical_login'),
    path('logout/', views.medical_logout, name='medical_logout'),

    # Profile Creation, Viewing, and Editing
    path('profile/create/', views.create_medical_profile, name='create_medical_profile'),
    path('profile/', views.view_medical_profile, name='view_medical_profile'),
    path('profile/edit/', views.edit_medical_profile, name='edit_medical_profile'),

    # Main Dashboard
    path('dashboard/', views.medical_dashboard, name='medical_dashboard'),
    path('billing/history/', billing_history_view, name='billing_history'),

    path('prescription/<int:pk>/', views.PrescriptionDetailView.as_view(), name='prescription_detail'),
    path('prescription/<int:pk>/dispense/', views.dispense_prescription, name='dispense_prescription'),
     path('prescription/history/', views.prescription_history, name='prescription_history'),

    # --- ADD THE FOLLOWING URLS FOR MEDICINE MANAGEMENT ---
    path('medicines/', views.medicine_list_view, name='medicine_list'),
    path('medicines/create/', views.medicine_create_view, name='medicine_create'),
    path('medicines/<int:pk>/update/', views.medicine_update_view, name='medicine_update'),
    path('medicines/<int:pk>/delete/', views.medicine_delete_view, name='medicine_delete'),
    
]
