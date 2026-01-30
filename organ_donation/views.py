from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db import transaction

from patient.models import PatientProfile
from doctor.models import DoctorProfile
from .models import (
    OrganDonation, OrganRequest, OrganTransaction, 
    DoctorApproval, OrganType, BloodType
)
from .forms import (
    OrganDonationForm, OrganRequestForm, OrganMatchingForm,
    DoctorApprovalForm, OrganTransactionForm,
    FilterOrganDonationForm, FilterOrganRequestForm
)


# ==================== DASHBOARD VIEW ====================

@login_required(login_url='login')
def organ_donation_dashboard(request):
    """Main dashboard for organ donation system"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
        user_donations_count = OrganDonation.objects.filter(donor=patient_profile).count()
        user_requests_count = OrganRequest.objects.filter(requester=patient_profile).count()
        available_organs_count = OrganDonation.objects.filter(status='available').count()
        pending_requests_count = OrganRequest.objects.filter(status='pending').count()
        
        context = {
            'user_donations_count': user_donations_count,
            'user_requests_count': user_requests_count,
            'available_organs_count': available_organs_count,
            'pending_requests_count': pending_requests_count,
        }
    except PatientProfile.DoesNotExist:
        context = {}
    
    return render(request, 'organ_donation/dashboard.html', context)


# ==================== ORGAN DONATION VIEWS ====================

class OrganDonationListView(LoginRequiredMixin, ListView):
    """List all available organ donations"""
    model = OrganDonation
    template_name = 'organ_donation/donation_list.html'
    context_object_name = 'donations'
    paginate_by = 10
    login_url = 'login'
    
    def get_queryset(self):
        # Only show available donations (hide matched/completed/cancelled)
        queryset = OrganDonation.objects.filter(status='available').select_related(
            'donor', 'organ_type', 'blood_type'
        )
        
        # Apply filters
        organ_type = self.request.GET.get('organ_type')
        blood_type = self.request.GET.get('blood_type')
        
        if organ_type:
            queryset = queryset.filter(organ_type_id=organ_type)
        if blood_type:
            queryset = queryset.filter(blood_type_id=blood_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FilterOrganDonationForm(self.request.GET)
        return context


class OrganDonationDetailView(LoginRequiredMixin, DetailView):
    """View detailed information about an organ donation"""
    model = OrganDonation
    template_name = 'organ_donation/donation_detail.html'
    context_object_name = 'donation'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        donation = self.get_object()
        
        # Get matching requests
        context['matching_requests'] = OrganRequest.objects.filter(
            organ_type=donation.organ_type,
            status='pending'
        ).exclude(requester=donation.donor).select_related('requester')
        
        return context


@login_required(login_url='login')
def register_organ_donation(request):
    """View for registering organ donation"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Please complete your patient profile first.')
        return redirect('patient:patient_profile')
    
    if request.method == 'POST':
        form = OrganDonationForm(request.POST)
        if form.is_valid():
            try:
                donation = form.save(commit=False)
                donation.donor = patient_profile
                donation.full_clean()
                donation.save()
                messages.success(request, 'Organ donation registered successfully!')
                return redirect('organ_donation:my_donations')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = OrganDonationForm()
    
    return render(request, 'organ_donation/register_donation.html', {'form': form})


@login_required(login_url='login')
def my_organ_donations(request):
    """View patient's own organ donations"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    donations = OrganDonation.objects.filter(donor=patient_profile).select_related(
        'organ_type', 'blood_type', 'matched_request', 'transaction'
    )
    
    context = {
        'donations': donations,
        'total_donations': donations.count(),
        'available_donations': donations.filter(status='available').count(),
        'completed_donations': donations.filter(status='completed').count(),
    }
    
    return render(request, 'organ_donation/my_donations.html', context)


@login_required(login_url='login')
def matched_donations_for_donor(request):
    """View matched donations with recipient contact info (for donors)"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    # Get donations that are matched (status='matched')
    matched_donations = OrganDonation.objects.filter(
        donor=patient_profile,
        status='matched'
    ).select_related(
        'organ_type', 'blood_type', 'matched_request__requester'
    )
    
    context = {
        'matched_donations': matched_donations,
        'total_matched': matched_donations.count(),
    }
    
    return render(request, 'organ_donation/matched_donations_donor.html', context)


@login_required(login_url='login')
def view_recipient_info(request, donation_id):
    """View recipient contact information for a matched donation"""
    donation = get_object_or_404(OrganDonation, pk=donation_id)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    # Verify donation belongs to logged-in user
    if donation.donor != patient_profile:
        messages.error(request, 'You do not have permission to view this donation.')
        return redirect('organ_donation:matched_donations_donor')
    
    # Donation must be matched
    if donation.status != 'matched' or not donation.matched_request:
        messages.error(request, 'This donation is not matched.')
        return redirect('organ_donation:matched_donations_donor')
    
    recipient = donation.matched_request.requester
    
    context = {
        'donation': donation,
        'recipient': recipient,
        'matched_request': donation.matched_request,
    }
    
    return render(request, 'organ_donation/recipient_info.html', context)


@login_required(login_url='login')
def confirm_transplant(request, donation_id):
    """Donor confirms that transplant has been completed"""
    donation = get_object_or_404(OrganDonation, pk=donation_id)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('organ_donation:matched_donations_donor')
    
    # Verify donation belongs to logged-in user
    if donation.donor != patient_profile:
        messages.error(request, 'You do not have permission to confirm this donation.')
        return redirect('organ_donation:matched_donations_donor')
    
    if donation.status != 'matched' or not donation.matched_request:
        messages.error(request, 'This donation is not matched.')
        return redirect('organ_donation:matched_donations_donor')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mark donation and request as completed
                donation.complete_donation()
                donation.matched_request.complete_request()
                
                # Create transaction record
                OrganTransaction.objects.create(
                    donation=donation,
                    request=donation.matched_request,
                    donor=donation.donor,
                    recipient=donation.matched_request.requester,
                    organ_type=donation.organ_type,
                    status='completed'
                )
                
                messages.success(request, 'Transplant confirmed successfully!')
                return redirect('organ_donation:my_donations')
        except Exception as e:
            messages.error(request, f'Error confirming transplant: {str(e)}')
    
    return render(request, 'organ_donation/confirm_transplant.html', {
        'donation': donation,
        'recipient': donation.matched_request.requester,
    })


@login_required(login_url='login')
def cancel_donation(request, pk):
    """Cancel an organ donation"""
    donation = get_object_or_404(OrganDonation, pk=pk)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    if donation.donor != patient_profile:
        messages.error(request, 'You do not have permission to cancel this donation.')
        return redirect('organ_donation:my_donations')
    
    if donation.status == 'cancelled':
        messages.warning(request, 'This donation is already cancelled.')
        return redirect('organ_donation:my_donations')
    
    if request.method == 'POST':
        donation.cancel_donation()
        messages.success(request, 'Organ donation cancelled successfully.')
        return redirect('organ_donation:my_donations')
    
    return render(request, 'organ_donation/confirm_cancel_donation.html', {'donation': donation})


# ==================== ORGAN REQUEST VIEWS ====================

class OrganRequestListView(LoginRequiredMixin, ListView):
    """List all pending organ requests"""
    model = OrganRequest
    template_name = 'organ_donation/request_list.html'
    context_object_name = 'requests'
    paginate_by = 10
    login_url = 'login'
    
    def get_queryset(self):
        # Only show pending requests (hide accepted/completed/cancelled)
        queryset = OrganRequest.objects.filter(status='pending').select_related(
            'requester', 'organ_type', 'blood_type'
        ).order_by('-urgency', '-created_at')
        
        # Apply filters
        organ_type = self.request.GET.get('organ_type')
        blood_type = self.request.GET.get('blood_type')
        urgency = self.request.GET.get('urgency')
        
        if organ_type:
            queryset = queryset.filter(organ_type_id=organ_type)
        if blood_type:
            queryset = queryset.filter(blood_type_id=blood_type)
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FilterOrganRequestForm(self.request.GET)
        return context


class OrganRequestDetailView(LoginRequiredMixin, DetailView):
    """View detailed information about an organ request"""
    model = OrganRequest
    template_name = 'organ_donation/request_detail.html'
    context_object_name = 'request'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organ_request = self.get_object()
        
        # Get matching donations
        context['matching_donations'] = OrganDonation.objects.filter(
            organ_type=organ_request.organ_type,
            status='available'
        ).exclude(donor=organ_request.requester).select_related('donor')
        
        return context


@login_required(login_url='login')
def request_organ(request):
    """View for requesting an organ"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Please complete your patient profile first.')
        return redirect('patient:patient_profile')
    
    if request.method == 'POST':
        form = OrganRequestForm(request.POST)
        if form.is_valid():
            try:
                organ_request = form.save(commit=False)
                organ_request.requester = patient_profile
                organ_request.full_clean()
                organ_request.save()
                messages.success(request, 'Organ request registered successfully!')
                return redirect('organ_donation:my_requests')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = OrganRequestForm()
    
    return render(request, 'organ_donation/request_organ.html', {'form': form})


@login_required(login_url='login')
def my_organ_requests(request):
    """View patient's own organ requests"""
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    organ_requests = OrganRequest.objects.filter(requester=patient_profile).select_related(
        'organ_type', 'blood_type', 'matched_donation'
    )
    
    context = {
        'requests': organ_requests,
        'total_requests': organ_requests.count(),
        'pending_requests': organ_requests.filter(status='pending').count(),
        'accepted_requests': organ_requests.filter(status='accepted').count(),
    }
    
    return render(request, 'organ_donation/my_requests.html', context)


@login_required(login_url='login')
def accept_donation(request, donation_id, request_id):
    """Accept a matched donation for a request"""
    donation = get_object_or_404(OrganDonation, pk=donation_id)
    organ_request = get_object_or_404(OrganRequest, pk=request_id)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('organ_donation:my_requests')
    
    if organ_request.requester != patient_profile:
        messages.error(request, 'You do not have permission to accept this donation.')
        return redirect('organ_donation:my_requests')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                organ_request.accept_donation(donation)
                # Create transaction directly (no doctor approval needed)
                org_transaction = OrganTransaction.objects.create(
                    donation=donation,
                    request=organ_request,
                    donor=donation.donor,
                    recipient=organ_request.requester,
                    organ_type=donation.organ_type,
                    status='completed'
                )
                messages.success(request, 'Organ matched and transplant completed successfully!')
                return redirect('organ_donation:my_requests')
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'organ_donation/confirm_accept_donation.html', {
        'donation': donation,
        'organ_request': organ_request
    })


@login_required(login_url='login')
def cancel_request(request, pk):
    """Cancel an organ request"""
    organ_request = get_object_or_404(OrganRequest, pk=pk)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient:patient_profile')
    
    if organ_request.requester != patient_profile:
        messages.error(request, 'You do not have permission to cancel this request.')
        return redirect('organ_donation:my_requests')
    
    if organ_request.status == 'cancelled':
        messages.warning(request, 'This request is already cancelled.')
        return redirect('organ_donation:my_requests')
    
    if request.method == 'POST':
        organ_request.cancel_request()
        messages.success(request, 'Organ request cancelled successfully.')
        return redirect('organ_donation:my_requests')
    
    return render(request, 'organ_donation/confirm_cancel_request.html', {'request': organ_request})
    #         donor=approval.donation.donor,
    #                     recipient=approval.request.requester,
    #                     organ_type=approval.donation.organ_type,
    #                     assigned_doctor=doctor_profile,
    #                     status='in_progress'
    #                 )
                    
    #                 messages.success(request, 'Match approved! Organ transaction initiated.')
    #             else:
    #                 approval_obj.reject(reason=form.cleaned_data.get('reason', ''))
    #                 messages.success(request, 'Match rejected.')
                
    #             return redirect('organ_donation:doctor_approvals')
    #         except Exception as e:
    #             messages.error(request, f'Error processing approval: {str(e)}')
    # else:
    #     form = DoctorApprovalForm(instance=approval)
    
    # return render(request, 'organ_donation/approve_match.html', {
    #     'form': form,
    #     'approval': approval
    # })


# ==================== TRANSACTION VIEWS ====================

@login_required(login_url='login')
def organ_transactions(request):
    """View all organ transactions"""
    try:
        doctor_profile = DoctorProfile.objects.filter(doctor=request.user).first()
        if not doctor_profile:
            raise DoctorProfile.DoesNotExist
        transactions = OrganTransaction.objects.filter(
            assigned_doctor=doctor_profile
        ).select_related('donor', 'recipient', 'organ_type', 'assigned_doctor')
    except DoctorProfile.DoesNotExist:
        try:
            patient_profile = PatientProfile.objects.filter(patient=request.user).first()
            if not patient_profile:
                raise PatientProfile.DoesNotExist
            transactions = OrganTransaction.objects.filter(
                Q(donor=patient_profile) | Q(recipient=patient_profile)
            ).select_related('donor', 'recipient', 'organ_type', 'assigned_doctor')
        except PatientProfile.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('patient:patient_profile')
    
    context = {
        'transactions': transactions,
        'total_transactions': transactions.count(),
        'completed_transactions': transactions.filter(status='completed').count(),
    }
    
    return render(request, 'organ_donation/transactions.html', context)


@login_required(login_url='login')
def complete_transaction(request, transaction_id):
    """Mark organ transaction as completed"""
    transaction_obj = get_object_or_404(OrganTransaction, pk=transaction_id)
    
    try:
        doctor_profile = DoctorProfile.objects.filter(doctor=request.user).first()
        if not doctor_profile:
            raise DoctorProfile.DoesNotExist
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Only doctors can complete transactions.')
        return redirect('organ_donation:transactions')
    
    if transaction_obj.assigned_doctor != doctor_profile:
        messages.error(request, 'You do not have permission to complete this transaction.')
        return redirect('organ_donation:transactions')
    
    if request.method == 'POST':
        form = OrganTransactionForm(request.POST, instance=transaction_obj)
        if form.is_valid():
            try:
                form.save()
                transaction_obj.complete_transaction()
                messages.success(request, 'Transaction completed successfully!')
                return redirect('organ_donation:transactions')
            except Exception as e:
                messages.error(request, f'Error completing transaction: {str(e)}')
    else:
        form = OrganTransactionForm(instance=transaction_obj)
    
    return render(request, 'organ_donation/complete_transaction.html', {
        'form': form,
        'transaction': transaction_obj
    })


# ==================== DONOR ACCEPT/REJECT VIEWS ====================

@login_required(login_url='login')
def donor_accept_request(request, request_id):
    """Donor accepts a matched request and locks the donation"""
    organ_request = get_object_or_404(OrganRequest, pk=request_id)
    
    try:
        patient_profile = PatientProfile.objects.filter(patient=request.user).first()
        if not patient_profile:
            raise PatientProfile.DoesNotExist
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('organ_donation:donation_list')
    
    # Find matching donation from this donor
    matching_donations = OrganDonation.objects.filter(
        donor=patient_profile,
        organ_type=organ_request.organ_type,
        status='available'
    )
    
    if not matching_donations.exists():
        messages.error(request, 'You do not have a matching available donation.')
        return redirect('organ_donation:request_list')
    
    donation = matching_donations.first()
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mark donation as matched
                donation.status = 'matched'
                donation.matched_request = organ_request
                donation.save()
                
                # Mark request as accepted
                organ_request.status = 'accepted'
                organ_request.matched_donation = donation
                organ_request.save()
                
                messages.success(request, f'Request accepted! Patient contact: {organ_request.requester.phone}')
                return redirect('organ_donation:my_donations')
        except Exception as e:
            messages.error(request, f'Error accepting request: {str(e)}')
    
    return render(request, 'organ_donation/donor_accept_request.html', {
        'donation': donation,
        'organ_request': organ_request,
        'patient': organ_request.requester,
    })


