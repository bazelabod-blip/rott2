from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.accounts.models import User
from apps.marketplace.models import Category, Service
from .models import Order
class OrderStateMachineTests(TestCase):
    def setUp(self):
        self.customer=User.objects.create_user(username='c',email='c@example.com',password='x',role='customer')
        self.provider=User.objects.create_user(username='p',email='p@example.com',password='x',role='provider')
        self.category=Category.objects.create(name='Design')
        self.service=Service.objects.create(provider=self.provider,category=self.category,title='Logo',description='Logo',price=100,delivery_time=2,status='active')
        self.order=Order.objects.create(customer=self.customer,provider=self.provider,service=self.service,title='Logo',description='Need logo',agreed_price=100,delivery_days=2)
    def test_acceptance_does_not_mark_payment_paid(self):
        self.order.transition_to(Order.STATUS_ACCEPTED)
        self.order.save()
        self.assertEqual(self.order.payment_status,'pending')
    def test_invalid_transition_rejected(self):
        with self.assertRaises(ValidationError):
            self.order.transition_to(Order.STATUS_COMPLETED)
