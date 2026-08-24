from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User
from .models import Category, Service, ProviderService

class ProviderActivationTests(TestCase):
    def setUp(self):
        self.category=Category.objects.create(name='Design')
        self.provider=User.objects.create_user(username='p', email='p@example.com', password='x', role='provider')
    def test_unverified_provider_cannot_add_service_backend(self):
        self.client.force_login(self.provider)
        response=self.client.post(reverse('marketplace:service_create'), {'title':'Logo','category':self.category.pk,'description':'x','price_type':'fixed','currency':'YER','price':'100','delivery_time':'2'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Service.objects.filter(title='Logo').exists())
    def test_verified_provider_can_add_service(self):
        profile=self.provider.provider_profile; profile.status='active'; profile.verification_status='verified'; profile.save()
        self.client.force_login(self.provider)
        response=self.client.post(reverse('marketplace:service_create'), {'title':'Logo','category':self.category.pk,'description':'x','price_type':'fixed','currency':'YER','price':'100','delivery_time':'2'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Service.objects.filter(title='Logo').exists())
    def test_unverified_provider_service_model_validation(self):
        service=Service(provider=self.provider, category=self.category, title='Catalog', description='x', price=10, delivery_time=1)
        provider_service=ProviderService(provider=self.provider.provider_profile, service=service, price=10)
        with self.assertRaises(ValidationError):
            provider_service.full_clean()

class SearchTests(TestCase):
    def setUp(self):
        self.category=Category.objects.create(name='Design')
        self.provider=User.objects.create_user(username='designer', email='d@example.com', password='x', role='provider')
        profile=self.provider.provider_profile; profile.status='active'; profile.verification_status='verified'; profile.city='Sanaa'; profile.district='Hadda'; profile.latitude='15.350000'; profile.longitude='44.200000'; profile.specialization='Logo Design'; profile.save()
        self.service=Service.objects.create(provider=self.provider, category=self.category, title='Logo Design', description='Branding', price=100, delivery_time=2, status='active')
    def test_global_search_backend_returns_public_database_results(self):
        from .search import filter_public_services, filter_public_providers, filter_public_categories
        self.assertIn(self.service, list(filter_public_services({'q':'Logo'})))
        self.assertIn(self.provider, list(filter_public_providers({'q':'Logo'})))
        self.assertIn(self.category, list(filter_public_categories({'q':'Design'})))
    def test_provider_search_filters_by_city_district_and_distance(self):
        from .search import filter_public_providers
        providers = filter_public_providers({'q':'Logo','city':'Sanaa','district':'Hadda','lat':'15.35','lng':'44.20','radius':'5'})
        self.assertIn(self.provider, providers)
