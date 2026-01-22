from django.urls import path
from . import views

app_name = 'organ_donation'

urlpatterns = [
    # Dashboard
    path('', views.organ_donation_dashboard, name='dashboard'),
    
    # Organ Donation URLs
    path('donations/', views.OrganDonationListView.as_view(), name='donation_list'),
    path('donations/<int:pk>/', views.OrganDonationDetailView.as_view(), name='donation_detail'),
    path('donations/register/', views.register_organ_donation, name='register_donation'),
    path('my-donations/', views.my_organ_donations, name='my_donations'),
    path('matched-donations/', views.matched_donations_for_donor, name='matched_donations_donor'),
    path('donations/<int:donation_id>/recipient-info/', views.view_recipient_info, name='recipient_info'),
    path('donations/<int:donation_id>/confirm-transplant/', views.confirm_transplant, name='confirm_transplant'),
    path('donations/<int:pk>/cancel/', views.cancel_donation, name='cancel_donation'),
    
    # Organ Request URLs
    path('requests/', views.OrganRequestListView.as_view(), name='request_list'),
    path('requests/<int:pk>/', views.OrganRequestDetailView.as_view(), name='request_detail'),
    path('requests/new/', views.request_organ, name='request_organ'),
    path('my-requests/', views.my_organ_requests, name='my_requests'),
    path('requests/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    
    # Accept Donation
    path('donations/<int:donation_id>/requests/<int:request_id>/accept/', 
         views.accept_donation, name='accept_donation'),
    
    # Donor Accept Request
    path('requests/<int:request_id>/donor-accept/', 
         views.donor_accept_request, name='donor_accept_request'),
    
    # Transaction URLs
    path('transactions/', views.organ_transactions, name='transactions'),
]
