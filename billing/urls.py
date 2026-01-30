from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('register/', views.accountant_register, name='accountant_register'),
    path('profile/create/', views.create_accountant_profile, name='create_accountant_profile'),
    path('profile/', views.view_accountant_profile, name='view_accountant_profile'),
    path('bills/unpaid/', views.process_unpaid_bills, name='process_unpaid_bills'),
    path('bill/<int:pk>/update/', views.update_bill_view, name='update_bill'),
    path('bills/history/', views.paid_bills_history, name='paid_bills_history'),

]
