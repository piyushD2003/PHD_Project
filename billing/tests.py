from django.test import TestCase
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from billing.models import Billing

class BillingViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='patient', password='password123')
        self.client.login(username='patient', password='password123')

    def test_billing_list_view(self):
        response = self.client.get(reverse('billing:billing_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'billing/billing_list.html')

    def test_create_billing_view_get(self):
        response = self.client.get(reverse('billing:create_billing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'billing/billing_form.html')

    def test_create_billing_view_post(self):
        data = {
            'total_amount': 500,
            'paid_amount': 300,
            'balance_amount': 200,
            # Add other required fields if any
        }
        response = self.client.post(reverse('billing:create_billing'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Billing.objects.count(), 1)

    def test_edit_billing_view(self):
        billing = Billing.objects.create(
            patient=self.user,
            total_amount=1000,
            paid_amount=500,
            balance_amount=500
        )
        response = self.client.get(reverse('billing:edit_billing', args=[billing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'billing/billing_form.html')

    def test_delete_billing_view(self):
        billing = Billing.objects.create(
            patient=self.user,
            total_amount=1000,
            paid_amount=500,
            balance_amount=500
        )
        response = self.client.post(reverse('billing:delete_billing', args=[billing.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Billing.objects.filter(id=billing.id).exists())
