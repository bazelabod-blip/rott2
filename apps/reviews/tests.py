from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.marketplace.models import Category, Service
from apps.orders.models import Order
from .models import Review
class ReviewIntegrityTests(TestCase):
    def test_review_tied_to_completed_order_customer(self):
        c=User.objects.create_user(username='c2',email='c2@example.com',password='x',role='customer')
        p=User.objects.create_user(username='p2',email='p2@example.com',password='x',role='provider')
        cat=Category.objects.create(name='Writing')
        svc=Service.objects.create(provider=p,category=cat,title='Copy',description='Copy',price=50,delivery_time=1,status='active')
        order=Order.objects.create(customer=c,provider=p,service=svc,title='Copy',description='x',agreed_price=50,delivery_days=1,status=Order.STATUS_PENDING)
        review=Review(order=order,customer=c,provider=p,service=svc,service_rating=5,provider_rating=5,comment='Great')
        with self.assertRaises(ValidationError):
            review.full_clean()
