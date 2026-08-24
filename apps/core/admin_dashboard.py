from decimal import Decimal
from django.contrib import admin
from django.db.models import Sum


def install_admin_dashboard():
    original_index = admin.site.index
    def index(request, extra_context=None):
        from apps.accounts.models import User, ProviderProfile
        from apps.marketplace.models import Service
        from apps.orders.models import Order
        from apps.payments.models import Payment
        extra_context = extra_context or {}
        paid = Payment.objects.filter(status=Payment.STATUS_PAID).aggregate(
            sales=Sum('amount'), commission=Sum('commission_amount'), earnings=Sum('provider_net_amount')
        )
        extra_context['platform_stats'] = {
            'users': User.objects.count(),
            'providers': ProviderProfile.objects.count(),
            'customers': User.objects.filter(role='customer').count(),
            'verified_providers': ProviderProfile.objects.filter(verification_status='verified').count(),
            'pending_verification': ProviderProfile.objects.filter(verification_status='pending_review').count(),
            'total_services': Service.objects.count(),
            'active_services': Service.objects.filter(status='active').count(),
            'total_orders': Order.objects.count(),
            'completed_orders': Order.objects.filter(status=Order.STATUS_COMPLETED).count(),
            'pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
            'cancelled_orders': Order.objects.filter(status=Order.STATUS_CANCELLED).count(),
            'total_sales': paid['sales'] or Decimal('0'),
            'platform_commission': paid['commission'] or Decimal('0'),
            'provider_earnings': paid['earnings'] or Decimal('0'),
        }
        return original_index(request, extra_context=extra_context)
    admin.site.index = index
    admin.site.site_header = 'لوحة إدارة سوق الخدمات'
    admin.site.site_title = 'إدارة سوق الخدمات'
    admin.site.index_title = 'لوحة التحكم'
