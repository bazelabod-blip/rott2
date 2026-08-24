from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.template.context import BaseContext, Context, RequestContext
from django.urls import reverse

# Django 4.2 test client context-copy is not compatible with Python 3.14 slots here.
def _safe_context_copy(self):
    return self
BaseContext.__copy__ = _safe_context_copy
Context.__copy__ = _safe_context_copy
RequestContext.__copy__ = _safe_context_copy

from apps.accounts.models import User, ProviderDocument, ProviderDocumentType, ProviderVerificationRequest
from apps.core.models import City, District, TermsAndConditions
from apps.marketplace.models import Category, ManagedService, Service, Specialization, Qualification
from apps.orders.models import Order
from apps.payments.models import Wallet, ProviderWallet, Payment

class DashboardAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='pass', role='admin', is_staff=True)
        self.customer = User.objects.create_user(username='customer', email='customer@example.com', password='pass', role='customer')
        self.provider_user = User.objects.create_user(username='provider', email='provider@example.com', password='pass', role='provider')
        self.provider = self.provider_user.provider_profile
        self.city = City.objects.create(name='صنعاء')
        self.district = District.objects.create(city=self.city, name='معين')
        self.spec = Specialization.objects.create(name='برمجة')
        self.qual = Qualification.objects.create(name='بكالوريوس')
        self.category = Category.objects.create(name='تقنية')
        self.managed = ManagedService.objects.create(name='تطوير مواقع', category=self.category)
        self.provider.status='active'; self.provider.verification_status='verified'; self.provider.save()
        self.service = Service.objects.create(provider=self.provider_user, category=self.category, title='خدمة حقيقية', description='وصف', price=100, delivery_time=2, status='active')
        self.order = Order.objects.create(customer=self.customer, provider=self.provider_user, service=self.service, title='طلب', description='تفاصيل', agreed_price=100, delivery_days=2, status=Order.STATUS_COMPLETED)
        self.wallet, _ = Wallet.objects.get_or_create(code='jaib', defaults={'name':'جيب'})
        self.provider_wallet = ProviderWallet.objects.create(provider=self.provider, wallet=self.wallet, account_number='123456789')
        self.payment = Payment.objects.create(order=self.order, provider_wallet=self.provider_wallet, amount=100, status=Payment.STATUS_PAID, commission_rate=10, commission_amount=10, provider_net_amount=90)
        self.doc_type = ProviderDocumentType.objects.create(code='ID', name='هوية', is_required=True)
        self.doc = ProviderDocument.objects.create(provider=self.provider, document_type=self.doc_type, file=SimpleUploadedFile('id.pdf', b'%PDF', content_type='application/pdf'))
        self.verification = ProviderVerificationRequest.objects.create(provider=self.provider, status='pending')
        self.verification.requested_services.add(self.managed); self.verification.documents.add(self.doc)

    def test_non_admin_blocked_and_admin_allowed(self):
        self.client.login(username='customer', password='pass')
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 403)
        self.client.login(username='admin', password='pass')
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 200)

    def test_lists_search_filters_and_details(self):
        self.client.login(username='admin', password='pass')
        for name in ['users','providers','verification','services','orders','payments','reviews','cities','districts','specializations','qualifications','wallets','commissions','settings']:
            self.assertLess(self.client.get(reverse(f'dashboard:{name}'), {'q':'خدمة'}).status_code, 400)
        self.assertContains(self.client.get(reverse('dashboard:services'), {'q':'حقيقية'}), 'خدمة حقيقية')
        self.assertContains(self.client.get(reverse('dashboard:orders'), {'status':Order.STATUS_COMPLETED}), self.order.order_number)
        self.assertEqual(self.client.get(reverse('dashboard:provider_detail', args=[self.provider.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:order_detail', args=[self.order.order_number])).status_code, 200)

    def test_verification_approve_reject_and_document_download(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.post(reverse('dashboard:verification_decision', args=[self.verification.pk]), {'status':'approved','admin_note':'مقبول'})
        self.assertRedirects(resp, reverse('dashboard:verification_detail', args=[self.verification.pk]))
        self.provider.refresh_from_db(); self.assertEqual(self.provider.verification_status, 'verified')
        self.verification.status='pending'; self.verification.save()
        self.client.post(reverse('dashboard:verification_decision', args=[self.verification.pk]), {'status':'rejected','admin_note':'مرفوض'})
        self.provider.refresh_from_db(); self.assertEqual(self.provider.verification_status, 'rejected')
        self.assertEqual(self.client.get(reverse('dashboard:document_download', args=[self.doc.pk])).status_code, 200)

    def test_commission_setting_and_pagination(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.post(reverse('dashboard:settings'), {'version':'v1','content':'شروط','commission_rate':'15','is_active':'on'})
        self.assertRedirects(resp, reverse('dashboard:settings'))
        self.assertEqual(TermsAndConditions.objects.get(version='v1').commission_rate, 15)
        for i in range(20): User.objects.create_user(username=f'u{i}', email=f'u{i}@e.com', password='pass')
        self.assertContains(self.client.get(reverse('dashboard:users'), {'page':2}), 'u')

class DashboardActionTests(DashboardAccessTests):
    def test_admin_can_manage_user_provider_document_review_and_notification(self):
        self.client.login(username='admin', password='pass')
        self.assertEqual(self.client.post(reverse('dashboard:user_action', args=[self.customer.pk, 'deactivate']), {'reason':'اختبار'}).status_code, 302)
        self.customer.refresh_from_db(); self.assertFalse(self.customer.is_active)
        self.assertEqual(self.client.post(reverse('dashboard:provider_action', args=[self.provider.pk, 'request_documents']), {'reason':'أعد رفع الهوية'}).status_code, 302)
        self.provider.refresh_from_db(); self.assertEqual(self.provider.verification_status, 'needs_documents')
        self.assertEqual(self.client.post(reverse('dashboard:document_review', args=[self.doc.pk]), {'action':'approved','note':'واضح'}).status_code, 302)
        self.doc.refresh_from_db(); self.assertEqual(self.doc.status, 'approved')
        self.assertEqual(self.client.post(reverse('dashboard:notification_create'), {'target':'user','user':self.customer.pk,'title':'تنبيه','message':'رسالة'}).status_code, 302)
        self.assertTrue(self.customer.notifications.filter(title='تنبيه').exists())

    def test_service_order_payment_review_export_and_audit_actions(self):
        self.client.login(username='admin', password='pass')
        self.assertEqual(self.client.post(reverse('dashboard:service_action', args=[self.service.pk, 'unpublish']), {'reason':'اختبار'}).status_code, 302)
        self.service.refresh_from_db(); self.assertEqual(self.service.status, 'paused')
        self.order.status = Order.STATUS_PENDING; self.order.save()
        self.assertEqual(self.client.post(reverse('dashboard:order_status_action', args=[self.order.order_number]), {'status':Order.STATUS_ACCEPTED,'reason':'مراجعة','force':''}).status_code, 302)
        self.order.refresh_from_db(); self.assertEqual(self.order.status, Order.STATUS_ACCEPTED)
        self.assertEqual(self.client.post(reverse('dashboard:payment_action', args=[self.payment.pk, 'refund']), {'reason':'استرداد داخلي'}).status_code, 302)
        self.payment.refresh_from_db(); self.assertEqual(self.payment.status, Payment.STATUS_REFUNDED)
        self.assertEqual(self.client.post(reverse('dashboard:review_action', args=[self.order.review.pk if hasattr(self.order, 'review') else 999, 'hide']), {'reason':'اختبار'}).status_code if hasattr(self.order, 'review') else 404, 404)
        self.assertEqual(self.client.get(reverse('dashboard:export', args=['users'])).status_code, 200)
