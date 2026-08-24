from pathlib import Path
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.accounts.models import User, ProviderProfile, ProviderVerificationRequest, ProviderDocument
from apps.core.models import City, District, TermsAndConditions
from apps.marketplace.models import Service, ManagedService, Specialization, Qualification, ProviderService
from apps.orders.models import Order
from apps.payments.models import Payment, CommissionRecord, Wallet, ProviderWallet
from apps.reviews.models import Review
from .forms import VerificationDecisionForm, CityForm, DistrictForm, ManagedServiceForm, SpecializationForm, QualificationForm, WalletForm, TermsForm
from .permissions import dashboard_required, can_access_dashboard
from .services.statistics import platform_statistics, provider_statistics

PER_PAGE = 15

def _paginate(request, qs, per_page=PER_PAGE):
    return Paginator(qs, per_page).get_page(request.GET.get('page'))

def _common(request, title):
    unread = request.user.notifications.filter(is_read=False).count() if hasattr(request.user, 'notifications') else 0
    return {'page_title': title, 'unread_notifications': unread}

def _search(qs, q, fields):
    if not q: return qs
    query = Q()
    for field in fields: query |= Q(**{f'{field}__icontains': q})
    return qs.filter(query)

@dashboard_required
def index(request):
    ctx = _common(request, 'لوحة التحكم الرئيسية')
    ctx.update(platform_statistics())
    return render(request, 'dashboard/dashboard.html', ctx)

@dashboard_required
def users_list(request):
    qs = User.objects.select_related('location_city','location_district').order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['username','email','first_name','last_name','phone'])
    if request.GET.get('role'): qs = qs.filter(role=request.GET['role'])
    if request.GET.get('active') in {'0','1'}: qs = qs.filter(is_active=request.GET['active'] == '1')
    ctx = _common(request, 'المستخدمون'); ctx.update({'page_obj': _paginate(request, qs), 'roles': User.ROLE_CHOICES})
    return render(request, 'dashboard/users/list.html', ctx)

@dashboard_required
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related('location_city','location_district'), pk=pk)
    ctx = _common(request, 'تفاصيل المستخدم'); ctx['user_obj'] = user
    ctx['orders_as_customer'] = Order.objects.filter(customer=user).select_related('provider','service')[:20]
    ctx['orders_as_provider'] = Order.objects.filter(provider=user).select_related('customer','service')[:20]
    ctx['reviews_given'] = Review.objects.filter(customer=user).select_related('provider','service','order')[:20]
    ctx['reviews_received'] = Review.objects.filter(provider=user).select_related('customer','service','order')[:20]
    if hasattr(user, 'provider_profile'):
        return redirect('dashboard:provider_detail', pk=user.provider_profile.pk)
    return render(request, 'dashboard/users/detail.html', ctx)

@dashboard_required
def providers_list(request):
    qs = ProviderProfile.objects.select_related('user','location_city','location_district').prefetch_related('specializations','qualification_choices').annotate(services_total=Count('user__services', distinct=True), orders_total_db=Count('user__orders_as_provider', distinct=True), avg_rating_db=Avg('user__reviews_received__provider_rating')).order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['user__username','user__email','display_name','business_name','phone'])
    for key, field in [('verification_status','verification_status'),('status','status'),('city','location_city_id'),('district','location_district_id'),('specialization','specializations__id')]:
        if request.GET.get(key): qs = qs.filter(**{field: request.GET[key]})
    ctx = _common(request, 'مقدمو الخدمات'); ctx.update({'page_obj': _paginate(request, qs.distinct()), 'verification_choices': ProviderProfile.VERIFICATION_STATUS_CHOICES, 'status_choices': ProviderProfile.STATUS_CHOICES, 'cities': City.objects.filter(is_active=True), 'districts': District.objects.filter(is_active=True), 'specializations': Specialization.objects.filter(is_active=True)})
    return render(request, 'dashboard/providers/list.html', ctx)

@dashboard_required
def provider_detail(request, pk):
    provider = get_object_or_404(ProviderProfile.objects.select_related('user','location_city','location_district').prefetch_related('specializations','qualification_choices','documents__document_type','wallet_accounts__wallet'), pk=pk)
    ctx = _common(request, 'ملف مقدم الخدمة الإداري'); ctx.update({'provider': provider, 'stats': provider_statistics(provider), 'services': Service.objects.filter(provider=provider.user).select_related('category')[:30], 'provider_services': ProviderService.objects.filter(provider=provider).select_related('catalog_service','service')[:30], 'orders': Order.objects.filter(provider=provider.user).select_related('customer','service')[:30], 'reviews': Review.objects.filter(provider=provider.user).select_related('customer','service','order')[:30], 'payments': Payment.objects.filter(order__provider=provider.user).select_related('order','provider_wallet__wallet')[:30]})
    return render(request, 'dashboard/providers/detail.html', ctx)

@dashboard_required
def verification_list(request):
    qs = ProviderVerificationRequest.objects.select_related('provider__user','reviewed_by').prefetch_related('requested_services','documents__document_type').order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['provider__user__username','provider__user__email','provider__display_name','provider__business_name'])
    if request.GET.get('status'): qs = qs.filter(status=request.GET['status'])
    ctx = _common(request, 'طلبات التوثيق'); ctx.update({'page_obj': _paginate(request, qs), 'status_choices': ProviderVerificationRequest.STATUS_CHOICES})
    return render(request, 'dashboard/verification/list.html', ctx)

@dashboard_required
def verification_detail(request, pk):
    verification = get_object_or_404(ProviderVerificationRequest.objects.select_related('provider__user','provider__location_city','provider__location_district','reviewed_by').prefetch_related('requested_services','documents__document_type','provider__specializations','provider__qualification_choices','provider__wallet_accounts__wallet'), pk=pk)
    return render(request, 'dashboard/verification/detail.html', {**_common(request, 'تفاصيل طلب التوثيق'), 'verification': verification, 'form': VerificationDecisionForm(instance=verification)})

@dashboard_required
@require_POST
def verification_decision(request, pk):
    verification = get_object_or_404(ProviderVerificationRequest.objects.select_related('provider'), pk=pk)
    form = VerificationDecisionForm(request.POST, instance=verification)
    if not form.is_valid(): messages.error(request, 'تحقق من بيانات القرار.'); return redirect('dashboard:verification_detail', pk=pk)
    with transaction.atomic():
        verification = form.save(commit=False); verification.reviewed_by = request.user; verification.reviewed_at = timezone.now(); verification.save(); form.save_m2m()
        profile = verification.provider; profile.admin_notes = verification.admin_note
        if verification.status == 'approved':
            for managed in verification.requested_services.filter(is_active=True): ProviderService.objects.update_or_create(provider=profile, catalog_service=managed, defaults={'price': 0, 'is_active': True, 'approval_status': 'active'})
            profile.status='active'; profile.verification_status='verified'; profile.verified_by=request.user; profile.verified_at=timezone.now()
        elif verification.status == 'rejected': profile.status='inactive'; profile.verification_status='rejected'
        elif verification.status == 'needs_documents': profile.status='inactive'; profile.verification_status='needs_documents'
        elif verification.status == 'pending': profile.verification_status='pending_review'
        profile.save()
    messages.success(request, 'تم حفظ قرار التوثيق وتحديث ملف مقدم الخدمة.')
    return redirect('dashboard:verification_detail', pk=pk)

@dashboard_required
def document_download(request, pk):
    document = get_object_or_404(ProviderDocument, pk=pk)
    filename = Path(document.file.name).name
    try:
        if document.file and document.file.storage.exists(document.file.name): return FileResponse(document.file.open('rb'), as_attachment=False, filename=filename)
    except FileNotFoundError as exc: raise Http404('المستند غير موجود.') from exc
    raise Http404('المستند غير موجود.')

@dashboard_required
def services_list(request):
    qs = Service.objects.select_related('provider','category').annotate(real_orders=Count('orders')).order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['title','provider__username','provider__email','category__name'])
    if request.GET.get('status'): qs = qs.filter(status=request.GET['status'])
    return render(request, 'dashboard/services/list.html', {**_common(request, 'الخدمات'), 'page_obj': _paginate(request, qs), 'status_choices': Service.STATUS_CHOICES})

@dashboard_required
def orders_list(request):
    qs = Order.objects.select_related('customer','provider','service').order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['order_number','title','customer__username','provider__username','service__title'])
    if request.GET.get('status'): qs = qs.filter(status=request.GET['status'])
    return render(request, 'dashboard/orders/list.html', {**_common(request, 'الطلبات'), 'page_obj': _paginate(request, qs), 'status_choices': Order.STATUS_CHOICES})

@dashboard_required
def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.select_related('customer','provider','service'), order_number=order_number)
    return render(request, 'dashboard/orders/detail.html', {**_common(request, 'تفاصيل الطلب'), 'order': order, 'payments': order.payments.select_related('provider_wallet__wallet'), 'messages_list': order.messages.select_related('sender')[:50], 'deliveries': order.deliveries.all()})

@dashboard_required
def payments_list(request):
    qs = Payment.objects.select_related('order','order__customer','order__provider','provider_wallet__wallet').order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['transaction_id','order__order_number','order__customer__username','order__provider__username'])
    if request.GET.get('status'): qs = qs.filter(status=request.GET['status'])
    return render(request, 'dashboard/payments/list.html', {**_common(request, 'المدفوعات'), 'page_obj': _paginate(request, qs), 'status_choices': Payment.STATUS_CHOICES})

@dashboard_required
def commissions_list(request):
    qs = CommissionRecord.objects.select_related('order','payment','order__provider').order_by('-created_at')
    return render(request, 'dashboard/payments/commissions.html', {**_common(request, 'العمولات'), 'page_obj': _paginate(request, qs), 'active_terms': TermsAndConditions.objects.filter(is_active=True).first()})

@dashboard_required
def wallets_list(request):
    qs = Wallet.objects.annotate(accounts_total=Count('provider_accounts')).order_by('display_order','name')
    return render(request, 'dashboard/payments/wallets.html', {**_common(request, 'المحافظ الإلكترونية'), 'page_obj': _paginate(request, qs), 'form': WalletForm()})

@dashboard_required
def reviews_list(request):
    qs = Review.objects.select_related('customer','provider','service','order').order_by('-created_at')
    qs = _search(qs, request.GET.get('q'), ['comment','customer__username','provider__username','service__title','order__order_number'])
    return render(request, 'dashboard/reviews/list.html', {**_common(request, 'التقييمات'), 'page_obj': _paginate(request, qs)})

def manage_model_list(slug, title, model, form_class):
    @dashboard_required
    def view(request):
        instance = get_object_or_404(model, pk=request.GET.get('edit')) if request.GET.get('edit') else None
        if request.method == 'POST':
            instance = get_object_or_404(model, pk=request.POST.get('pk')) if request.POST.get('pk') else None
            form = form_class(request.POST, instance=instance)
            if form.is_valid(): form.save(); messages.success(request, 'تم حفظ البيانات بنجاح.'); return redirect(f'dashboard:{slug}')
            messages.error(request, 'تعذر حفظ البيانات. تحقق من الحقول.')
        else: form = form_class(instance=instance)
        qs = _search(model.objects.all(), request.GET.get('q'), ['name']) if hasattr(model, 'name') else model.objects.all()
        return render(request, 'dashboard/settings/model_list.html', {**_common(request, title), 'page_obj': _paginate(request, qs), 'form': form, 'object_name': title, 'edit_obj': instance})
    return view

@dashboard_required
def settings_view(request):
    if request.method == 'POST':
        form = TermsForm(request.POST)
        if form.is_valid(): form.save(); messages.success(request, 'تم حفظ إعدادات العمولة.'); return redirect('dashboard:settings')
    return render(request, 'dashboard/settings/index.html', {**_common(request, 'إعدادات المنصة'), 'terms': TermsAndConditions.objects.order_by('-created_at')[:10], 'form': TermsForm()})
