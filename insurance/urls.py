from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'insurance'

urlpatterns = [
    path('register/', views.insurance_register, name='insuranceRegister'),
    path('login/', views.insurance_login, name='insurance_login'),
    path('logout/', views.insurance_logout, name='insurance_logout'),

    path('profile/create/', views.create_insurance_profile, name='insurance_profile_create'),
    path('profile/', views.view_insurance_profile, name='view_profile'),
    path('profile/edit/', views.edit_insurance_profile, name='editInsuranceProfile'),  # ✅ Correct name
    path('dashboard/', views.insurance_dashboard_view, name='dashboard'),
    path('claim/<int:pk>/', views.claim_detail_view, name='claim_detail'),
    path('approved/', views.approved_claims_view, name='approved_claims'),
    path('rejected/', views.rejected_claims_view, name='rejected_claims'),

    path('claim/<int:pk>/update_status/', views.update_claim_status, name='update_claim_status'),
    path('bill/<int:pk>/pay/', views.pay_bill_view, name='pay_bill')
    # path('claim/<int:claim_pk>/pay_bill/<int:bill_pk>/', views.pay_bill_by_insurance, name='pay_bill_by_insurance'),
    # path('create/', views.create_insurance, name='create_insurance'),
    # path('all/', views.view_insurances, name='view_insurances'),
    # path('<int:insurance_id>/', views.insurance_detail, name='insurance_detail'),
    # # path('<int:insurance_id>/edit/', views.edit_insurance, name='edit_insurance'),
    # path('<int:insurance_id>/delete/', views.delete_insurance, name='delete_insurance'),
    
]
