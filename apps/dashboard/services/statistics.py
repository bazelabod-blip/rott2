from decimal import Decimal
from django.db.models import Count, Sum, Avg
from apps.accounts.models import User, ProviderProfile, ProviderVerificationRequest
from apps.marketplace.models import Service, ManagedService, Specialization, Qualification
from apps.orders.models import Order
from apps.payments.models import Payment, CommissionRecord, Wallet
from apps.reviews.models import Review
from apps.core.models import City, District, TermsAndConditions


def _money(value):
    return value or Decimal('0')


def platform_statistics():
    paid = Payment.objects.filter(status=Payment.STATUS_PAID).aggregate(
        total=Sum('amount'), commission=Sum('commission_amount'), net=Sum('provider_net_amount')
    )
    orders_by_status = dict(Order.objects.values_list('status').annotate(total=Count('id')))
    providers_by_verification = dict(ProviderProfile.objects.values_list('verification_status').annotate(total=Count('id')))
    return {
        'users_total': User.objects.count(),
        'customers_total': User.objects.filter(role='customer').count(),
        'providers_total': ProviderProfile.objects.count(),
        'providers_verified': providers_by_verification.get('verified', 0),
        'providers_pending': providers_by_verification.get('pending_review', 0),
        'providers_rejected': providers_by_verification.get('rejected', 0),
        'services_total': Service.objects.count(),
        'services_active': Service.objects.filter(status='active').count(),
        'managed_services_total': ManagedService.objects.count(),
        'orders_total': Order.objects.count(),
        'orders_new': orders_by_status.get(Order.STATUS_PENDING, 0),
        'orders_in_progress': orders_by_status.get(Order.STATUS_IN_PROGRESS, 0),
        'orders_completed': orders_by_status.get(Order.STATUS_COMPLETED, 0),
        'orders_cancelled': orders_by_status.get(Order.STATUS_CANCELLED, 0),
        'reviews_total': Review.objects.count(),
        'payments_total': _money(paid['total']),
        'commissions_total': _money(paid['commission']),
        'providers_net_total': _money(paid['net']),
        'wallets_total': Wallet.objects.count(),
        'cities_total': City.objects.count(),
        'districts_total': District.objects.count(),
        'specializations_total': Specialization.objects.count(),
        'qualifications_total': Qualification.objects.count(),
        'verification_requests_pending': ProviderVerificationRequest.objects.filter(status='pending').count(),
        'active_commission_rate': (TermsAndConditions.objects.filter(is_active=True).values_list('commission_rate', flat=True).first()),
        'charts': {
            'orders_by_status': list(Order.objects.values('status').annotate(total=Count('id')).order_by('status')),
            'payments_by_status': list(Payment.objects.values('status').annotate(total=Count('id')).order_by('status')),
            'top_services': list(Service.objects.annotate(total_orders=Count('orders')).filter(total_orders__gt=0).values('title','total_orders')[:8]),
        }
    }


def provider_statistics(provider_profile):
    provider_user = provider_profile.user
    orders = Order.objects.filter(provider=provider_user)
    paid = Payment.objects.filter(order__provider=provider_user, status=Payment.STATUS_PAID).aggregate(total=Sum('amount'), commission=Sum('commission_amount'), net=Sum('provider_net_amount'))
    return {
        'orders_total': orders.count(),
        'orders_completed': orders.filter(status=Order.STATUS_COMPLETED).count(),
        'orders_in_progress': orders.filter(status=Order.STATUS_IN_PROGRESS).count(),
        'orders_new': orders.filter(status=Order.STATUS_PENDING).count(),
        'orders_cancelled': orders.filter(status=Order.STATUS_CANCELLED).count(),
        'sales_total': _money(paid['total']),
        'commission_total': _money(paid['commission']),
        'net_total': _money(paid['net']),
        'rating_avg': Review.objects.filter(provider=provider_user).aggregate(avg=Avg('provider_rating'))['avg'] or 0,
        'reviews_total': Review.objects.filter(provider=provider_user).count(),
        'active_services': Service.objects.filter(provider=provider_user, status='active').count(),
    }
