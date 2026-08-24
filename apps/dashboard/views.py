import csv
from pathlib import Path
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.accounts.models import ProviderProfile, ProviderVerificationRequest, ProviderDocument, ProviderDocumentType
from apps.core.models import City, District, TermsAndConditions, Notification, AuditLog, TermsAcceptance
from apps.marketplace.models import Category, Service, ManagedService, Specialization, Qualification, ProviderService
from apps.orders.models import Order
from apps.payments.models import Payment, CommissionRecord, Wallet, ProviderWallet
from apps.reviews.models import Review
from .forms import (UserAdminForm, ProviderAdminForm, ReasonActionForm, OptionalReasonActionForm, VerificationDecisionForm, DocumentReviewForm, CategoryForm, ServiceForm, ProviderServiceForm, OrderStatusForm, NotificationForm, CityForm, DistrictForm, ManagedServiceForm, SpecializationForm, QualificationForm, WalletForm, TermsForm, GroupForm)
from .permissions import dashboard_required
from .services.statistics import platform_statistics, provider_statistics
from .services import actions

User = get_user_model()
PER_PAGE = 20
EXPORT_MAP = {
    'users': ('users.csv', ['id','username','email','phone','role','is_active','created_at']),
    'providers': ('providers.csv', ['id','user__username','display_name','business_name','status','verification_status','created_at']),
    'orders': ('orders.csv', ['order_number','customer__username','provider__username','title','agreed_price','status','payment_status','created_at']),
    'payments': ('payments.csv', ['id','transaction_id','order__order_number','amount','status','commission_amount','provider_net_amount','created_at']),
    'commissions': ('commissions.csv', ['order__order_number','commission_rate','gross_amount','commission_amount','provider_net_amount','created_at']),
    'reviews': ('reviews.csv', ['id','customer__username','provider__username','service__title','provider_rating','service_rating','is_public','created_at']),
    'services': ('services.csv', ['id','provider__username','category__name','title','price','status','orders_count','average_rating','created_at']),
}

def _paginate(request, qs, per_page=PER_PAGE): return Paginator(qs, per_page).get_page(request.GET.get('page'))
def _common(request, title):
    unread = request.user.notifications.filter(is_read=False).count() if hasattr(request.user, 'notifications') else 0
    return {'page_title': title, 'unread_notifications': unread}
def _search(qs, q, fields):
    if not q: return qs
    query=Q()
    for field in fields: query |= Q(**{f'{field}__icontains': q})
    return qs.filter(query)
def _date_filter(qs, request, field='created_at'):
    if request.GET.get('date_from'): qs=qs.filter(**{f'{field}__date__gte': request.GET['date_from']})
    if request.GET.get('date_to'): qs=qs.filter(**{f'{field}__date__lte': request.GET['date_to']})
    return qs
def _sort(qs, request, allowed, default):
    key=request.GET.get('sort', default)
    return qs.order_by(key if key in allowed else default)
def _redirect_back(request, fallback): return redirect(request.POST.get('next') or fallback)
def _can_delete_user(user): return not (user.orders_as_customer.exists() or user.orders_as_provider.exists() or user.reviewed_payments.exists())
def _value(obj, path):
    cur=obj
    for part in path.split('__'):
        cur=getattr(cur, part, '')
        if cur is None: return ''
    return cur

def _export_response(filename, qs, fields):
    resp=HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition']=f'attachment; filename="{filename}"'
    resp.write('\ufeff')
    writer=csv.writer(resp); writer.writerow(fields)
    for obj in qs[:5000]: writer.writerow([_value(obj, f) for f in fields])
    return resp

@dashboard_required
def index(request):
    ctx=_common(request,'مركز التحكم الإداري'); ctx.update(platform_statistics())
    ctx.update({
        'latest_users': User.objects.order_by('-created_at')[:5],
        'latest_providers': ProviderProfile.objects.select_related('user').order_by('-created_at')[:5],
        'latest_orders': Order.objects.select_related('customer','provider','service').order_by('-created_at')[:5],
        'latest_payments': Payment.objects.select_related('order').order_by('-created_at')[:5],
        'latest_reviews': Review.objects.select_related('customer','provider','service').order_by('-created_at')[:5],
        'latest_audits': AuditLog.objects.select_related('actor','content_type')[:8],
    })
    return render(request,'dashboard/dashboard.html',ctx)

@dashboard_required
def users_list(request, role=None):
    qs=User.objects.select_related('location_city','location_district')
    if role: qs=qs.filter(role=role)
    qs=_search(qs, request.GET.get('q'), ['username','email','first_name','last_name','phone'])
    if request.GET.get('role'): qs=qs.filter(role=request.GET['role'])
    if request.GET.get('active') in {'0','1'}: qs=qs.filter(is_active=request.GET['active']=='1')
    if request.GET.get('city'): qs=qs.filter(location_city_id=request.GET['city'])
    qs=_date_filter(qs, request); qs=_sort(qs, request, {'created_at','-created_at','username','-username','last_login','-last_login'}, '-created_at')
    return render(request,'dashboard/users/list.html',{**_common(request,'المستخدمون'),'page_obj':_paginate(request,qs),'roles':User.ROLE_CHOICES,'cities':City.objects.filter(is_active=True)})

@dashboard_required
def user_create(request):
    if request.method=='POST':
        form=UserAdminForm(request.POST)
        if form.is_valid():
            user=form.save(); user.set_unusable_password(); user.save(); actions.audit(request,'user_created',user,new={'username':user.username,'role':user.role}); messages.success(request,'تم إنشاء المستخدم.'); return redirect('dashboard:user_detail', pk=user.pk)
    else: form=UserAdminForm()
    return render(request,'dashboard/form.html',{**_common(request,'إضافة مستخدم'),'form':form,'submit_label':'حفظ المستخدم'})

@dashboard_required
def user_edit(request, pk):
    user=get_object_or_404(User, pk=pk); old={'role':user.role,'is_active':user.is_active,'email':user.email}
    if request.method=='POST':
        form=UserAdminForm(request.POST, instance=user)
        if form.is_valid():
            user=form.save(); actions.audit(request,'user_edited',user,old=old,new={'role':user.role,'is_active':user.is_active,'email':user.email}); messages.success(request,'تم تحديث المستخدم.'); return redirect('dashboard:user_detail', pk=user.pk)
    else: form=UserAdminForm(instance=user)
    return render(request,'dashboard/form.html',{**_common(request,'تعديل مستخدم'),'form':form,'submit_label':'حفظ التعديل'})

@dashboard_required
def user_detail(request, pk):
    user=get_object_or_404(User.objects.select_related('location_city','location_district'), pk=pk)
    ctx={**_common(request,'تفاصيل المستخدم'),'user_obj':user,'orders_as_customer':Order.objects.filter(customer=user).select_related('provider','service')[:30],'orders_as_provider':Order.objects.filter(provider=user).select_related('customer','service')[:30],'reviews_given':Review.objects.filter(customer=user).select_related('provider','service','order')[:30],'reviews_received':Review.objects.filter(provider=user).select_related('customer','service','order')[:30],'notifications_list':Notification.objects.filter(recipient=user)[:30],'audits':AuditLog.objects.filter(actor=user)[:30]}
    return render(request,'dashboard/users/detail.html',ctx)

@dashboard_required
@require_POST
def user_action(request, pk, action_name):
    user=get_object_or_404(User, pk=pk); reason=request.POST.get('reason','')
    try:
        if action_name in {'activate','deactivate','suspend','restore'}: actions.update_user_status(request,user,action_name,reason)
        elif action_name == 'change_role': actions.change_user_role(request,user,request.POST.get('role'),reason)
        elif action_name == 'delete':
            if _can_delete_user(user): actions.audit(request,'user_deleted',user,reason=reason); user.delete(); messages.success(request,'تم حذف المستخدم.'); return redirect('dashboard:users')
            actions.update_user_status(request,user,'deactivate',reason or 'تعطيل بدل الحذف لوجود بيانات مرتبطة')
        else: raise ValidationError('إجراء غير معروف.')
        messages.success(request,'تم تنفيذ الإجراء.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:user_detail', pk=pk)

@dashboard_required
@require_POST
def users_bulk_action(request):
    ids=request.POST.getlist('ids'); action=request.POST.get('action'); updated=0
    for user in User.objects.filter(pk__in=ids):
        try: actions.update_user_status(request,user,action,request.POST.get('reason','إجراء جماعي')); updated+=1
        except Exception: pass
    messages.success(request, f'تم تنفيذ الإجراء على {updated} مستخدم.')
    return redirect('dashboard:users')

@dashboard_required
def providers_list(request):
    qs=ProviderProfile.objects.select_related('user','location_city','location_district').prefetch_related('specializations','qualification_choices').annotate(services_total=Count('user__services',distinct=True),orders_total_db=Count('user__orders_as_provider',distinct=True),avg_rating_db=Avg('user__reviews_received__provider_rating'))
    qs=_search(qs,request.GET.get('q'),['user__username','user__email','display_name','business_name','phone'])
    for key, field in [('verification_status','verification_status'),('status','status'),('city','location_city_id'),('district','location_district_id'),('specialization','specializations__id')]:
        if request.GET.get(key): qs=qs.filter(**{field:request.GET[key]})
    qs=_date_filter(qs,request); qs=_sort(qs.distinct(),request,{'created_at','-created_at','average_rating','-average_rating','status','verification_status'},'-created_at')
    return render(request,'dashboard/providers/list.html',{**_common(request,'مقدمو الخدمات'),'page_obj':_paginate(request,qs),'verification_choices':ProviderProfile.VERIFICATION_STATUS_CHOICES,'status_choices':ProviderProfile.STATUS_CHOICES,'cities':City.objects.filter(is_active=True),'districts':District.objects.filter(is_active=True),'specializations':Specialization.objects.filter(is_active=True)})

@dashboard_required
def provider_edit(request, pk):
    provider=get_object_or_404(ProviderProfile, pk=pk); old={'status':provider.status,'verification_status':provider.verification_status}
    if request.method=='POST':
        form=ProviderAdminForm(request.POST, request.FILES, instance=provider)
        if form.is_valid(): provider=form.save(); actions.audit(request,'provider_edited',provider,old=old,new={'status':provider.status,'verification_status':provider.verification_status}); messages.success(request,'تم تحديث مقدم الخدمة.'); return redirect('dashboard:provider_detail', pk=provider.pk)
    else: form=ProviderAdminForm(instance=provider)
    return render(request,'dashboard/form.html',{**_common(request,'تعديل مقدم خدمة'),'form':form,'submit_label':'حفظ مقدم الخدمة'})

@dashboard_required
def provider_detail(request, pk):
    provider=get_object_or_404(ProviderProfile.objects.select_related('user','location_city','location_district').prefetch_related('specializations','qualification_choices','documents__document_type','wallet_accounts__wallet'), pk=pk)
    ctx={**_common(request,'ملف مقدم الخدمة الإداري'),'provider':provider,'stats':provider_statistics(provider),'services':Service.objects.filter(provider=provider.user).select_related('category')[:50],'provider_services':ProviderService.objects.filter(provider=provider).select_related('catalog_service','service')[:50],'orders':Order.objects.filter(provider=provider.user).select_related('customer','service')[:50],'reviews':Review.objects.filter(provider=provider.user).select_related('customer','service','order')[:50],'payments':Payment.objects.filter(order__provider=provider.user).select_related('order','provider_wallet__wallet')[:50],'terms_acceptances':TermsAcceptance.objects.filter(user=provider.user).select_related('terms')[:20],'audits':AuditLog.objects.filter(object_id=str(provider.pk))[:30]}
    return render(request,'dashboard/providers/detail.html',ctx)

@dashboard_required
@require_POST
def provider_action(request, pk, action_name):
    provider=get_object_or_404(ProviderProfile, pk=pk)
    try: actions.provider_action(request,provider,action_name,request.POST.get('reason','')); messages.success(request,'تم تنفيذ إجراء مقدم الخدمة.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:provider_detail', pk=pk)

@dashboard_required
def verification_list(request):
    qs=ProviderVerificationRequest.objects.select_related('provider__user','reviewed_by').prefetch_related('requested_services','documents__document_type')
    qs=_search(qs,request.GET.get('q'),['provider__user__username','provider__user__email','provider__display_name','provider__business_name'])
    if request.GET.get('status'): qs=qs.filter(status=request.GET['status'])
    return render(request,'dashboard/verification/list.html',{**_common(request,'إدارة التوثيق'),'page_obj':_paginate(request,qs.order_by('-created_at')),'status_choices':ProviderVerificationRequest.STATUS_CHOICES,'tabs':ProviderProfile.VERIFICATION_STATUS_CHOICES})

@dashboard_required
def verification_detail(request, pk):
    verification=get_object_or_404(ProviderVerificationRequest.objects.select_related('provider__user','provider__location_city','provider__location_district','reviewed_by').prefetch_related('requested_services','documents__document_type','provider__specializations','provider__qualification_choices','provider__wallet_accounts__wallet'), pk=pk)
    return render(request,'dashboard/verification/detail.html',{**_common(request,'تفاصيل طلب التوثيق'),'verification':verification,'form':VerificationDecisionForm(instance=verification),'document_types':ProviderDocumentType.objects.filter(is_active=True)})

@dashboard_required
@require_POST
def verification_decision(request, pk):
    verification=get_object_or_404(ProviderVerificationRequest.objects.select_related('provider'), pk=pk); form=VerificationDecisionForm(request.POST, instance=verification)
    if form.is_valid():
        try: actions.verification_action(request,verification,form.cleaned_data['status'],form.cleaned_data['admin_note']); messages.success(request,'تم حفظ قرار التوثيق مع Audit وNotification.')
        except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    else: messages.error(request,'تحقق من بيانات القرار.')
    return redirect('dashboard:verification_detail', pk=pk)

@dashboard_required
def documents_list(request):
    qs=ProviderDocument.objects.select_related('provider__user','document_type','reviewed_by')
    qs=_search(qs,request.GET.get('q'),['provider__user__username','document_type__name','review_note'])
    if request.GET.get('status'): qs=qs.filter(status=request.GET['status'])
    return render(request,'dashboard/documents/list.html',{**_common(request,'إدارة المستندات'),'page_obj':_paginate(request,qs.order_by('-created_at')),'status_choices':ProviderDocument.STATUS_CHOICES})

@dashboard_required
def document_detail(request, pk):
    doc=get_object_or_404(ProviderDocument.objects.select_related('provider__user','document_type','reviewed_by'), pk=pk)
    return render(request,'dashboard/documents/detail.html',{**_common(request,'تفاصيل مستند'),'document':doc,'form':DocumentReviewForm()})

@dashboard_required
@require_POST
def document_review(request, pk):
    doc=get_object_or_404(ProviderDocument, pk=pk); form=DocumentReviewForm(request.POST)
    if form.is_valid():
        try: actions.document_action(request,doc,form.cleaned_data['action'],form.cleaned_data['note']); messages.success(request,'تم تحديث حالة المستند.')
        except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:document_detail', pk=pk)

@dashboard_required
def document_download(request, pk):
    document=get_object_or_404(ProviderDocument, pk=pk); filename=Path(document.file.name).name
    try:
        if document.file and document.file.storage.exists(document.file.name): return FileResponse(document.file.open('rb'), as_attachment=False, filename=filename)
    except FileNotFoundError as exc: raise Http404('المستند غير موجود.') from exc
    raise Http404('المستند غير موجود.')

@dashboard_required
def categories_list(request): return manage_model_page(request,'categories','التصنيفات',Category,CategoryForm)
@dashboard_required
def services_list(request):
    qs=Service.objects.select_related('provider','category').annotate(real_orders=Count('orders'))
    qs=_search(qs,request.GET.get('q'),['title','provider__username','provider__email','category__name'])
    if request.GET.get('status'): qs=qs.filter(status=request.GET['status'])
    return render(request,'dashboard/services/list.html',{**_common(request,'إدارة الخدمات'),'page_obj':_paginate(request,_sort(qs,request,{'created_at','-created_at','title','-title','status','price','-price'},'-created_at')),'status_choices':Service.STATUS_CHOICES,'form':ServiceForm()})
@dashboard_required
def service_edit(request, pk=None):
    obj=get_object_or_404(Service, pk=pk) if pk else None
    if request.method=='POST':
        form=ServiceForm(request.POST,request.FILES,instance=obj)
        if form.is_valid(): obj=form.save(); actions.audit(request,'service_saved',obj); messages.success(request,'تم حفظ الخدمة.'); return redirect('dashboard:services')
    else: form=ServiceForm(instance=obj)
    return render(request,'dashboard/form.html',{**_common(request,'إدارة خدمة'),'form':form,'submit_label':'حفظ الخدمة'})
@dashboard_required
@require_POST
def service_action(request, pk, action_name):
    try: actions.service_action(request,get_object_or_404(Service, pk=pk),action_name,request.POST.get('reason','')); messages.success(request,'تم تحديث الخدمة.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:services')

@dashboard_required
def provider_services_list(request):
    qs=ProviderService.objects.select_related('provider__user','service','catalog_service')
    qs=_search(qs,request.GET.get('q'),['provider__user__username','service__title','catalog_service__name'])
    if request.GET.get('status'): qs=qs.filter(approval_status=request.GET['status'])
    return render(request,'dashboard/services/provider_services.html',{**_common(request,'خدمات مقدمي الخدمات'),'page_obj':_paginate(request,qs.order_by('-created_at')),'status_choices':ProviderService.STATUS_CHOICES,'form':ProviderServiceForm()})
@dashboard_required
@require_POST
def provider_service_action(request, pk, action_name):
    try: actions.service_action(request,get_object_or_404(ProviderService, pk=pk),action_name,request.POST.get('reason','')); messages.success(request,'تم تحديث خدمة مقدم الخدمة.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:provider_services')

@dashboard_required
def orders_list(request):
    qs=Order.objects.select_related('customer','provider','service')
    qs=_search(qs,request.GET.get('q'),['order_number','title','customer__username','provider__username','service__title'])
    if request.GET.get('status'): qs=qs.filter(status=request.GET['status'])
    qs=_date_filter(qs,request); qs=_sort(qs,request,{'created_at','-created_at','agreed_price','-agreed_price','status'},'-created_at')
    return render(request,'dashboard/orders/list.html',{**_common(request,'إدارة الطلبات'),'page_obj':_paginate(request,qs),'status_choices':Order.STATUS_CHOICES})
@dashboard_required
def order_detail(request, order_number):
    order=get_object_or_404(Order.objects.select_related('customer','provider','service'), order_number=order_number)
    return render(request,'dashboard/orders/detail.html',{**_common(request,'مركز إدارة الطلب'),'order':order,'payments':order.payments.select_related('provider_wallet__wallet'),'messages_list':order.messages.select_related('sender')[:50],'deliveries':order.deliveries.all(),'review':getattr(order,'review',None),'form':OrderStatusForm(initial={'status':order.status}),'audits':AuditLog.objects.filter(object_id=str(order.pk))[:30]})
@dashboard_required
@require_POST
def order_status_action(request, order_number):
    order=get_object_or_404(Order, order_number=order_number); form=OrderStatusForm(request.POST)
    if form.is_valid():
        try: actions.change_order_status(request,order,form.cleaned_data['status'],form.cleaned_data['reason'],form.cleaned_data['force']); messages.success(request,'تم تحديث حالة الطلب.')
        except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:order_detail', order_number=order_number)

@dashboard_required
def payments_list(request):
    qs=Payment.objects.select_related('order','order__customer','order__provider','provider_wallet__wallet')
    qs=_search(qs,request.GET.get('q'),['transaction_id','order__order_number','order__customer__username','order__provider__username','gateway','payment_method'])
    for key in ['status','payment_method','gateway']:
        if request.GET.get(key): qs=qs.filter(**{key:request.GET[key]})
    qs=_date_filter(qs,request); qs=_sort(qs,request,{'created_at','-created_at','amount','-amount','status'},'-created_at')
    return render(request,'dashboard/payments/list.html',{**_common(request,'إدارة المدفوعات'),'page_obj':_paginate(request,qs),'status_choices':Payment.STATUS_CHOICES})
@dashboard_required
def payment_detail(request, pk):
    payment=get_object_or_404(Payment.objects.select_related('order','order__customer','order__provider','provider_wallet__wallet','reviewed_by'), pk=pk)
    return render(request,'dashboard/payments/detail.html',{**_common(request,'تفاصيل دفعة'),'payment':payment,'audits':AuditLog.objects.filter(object_id=str(payment.pk))[:30]})
@dashboard_required
@require_POST
def payment_action(request, pk, action_name):
    payment=get_object_or_404(Payment, pk=pk)
    try:
        if action_name=='refund': actions.payment_refund(request,payment,request.POST.get('reason',''))
        elif action_name=='cancel': old=payment.status; payment.status=Payment.STATUS_CANCELLED; payment.review_note=request.POST.get('reason',''); payment.save(); actions.audit(request,'payment_cancelled',payment,old={'status':old},new={'status':payment.status},reason=payment.review_note)
        else: raise ValidationError('إجراء دفع غير مدعوم.')
        messages.success(request,'تم تنفيذ إجراء الدفع.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:payment_detail', pk=pk)

@dashboard_required
def commissions_list(request):
    qs=CommissionRecord.objects.select_related('order','payment','order__provider')
    qs=_search(qs,request.GET.get('q'),['order__order_number','order__provider__username'])
    qs=_date_filter(qs,request)
    earnings=Payment.objects.filter(status=Payment.STATUS_PAID).values('order__provider__username').annotate(gross=Sum('amount'),commission=Sum('commission_amount'),net=Sum('provider_net_amount')).order_by('-net')
    return render(request,'dashboard/payments/commissions.html',{**_common(request,'إدارة العمولات'),'page_obj':_paginate(request,qs.order_by('-created_at')),'active_terms':TermsAndConditions.objects.filter(is_active=True).first(),'earnings':earnings[:20]})
@dashboard_required
def wallets_list(request): return manage_model_page(request,'wallets','المحافظ الإلكترونية',Wallet,WalletForm)
@dashboard_required
def reviews_list(request):
    qs=Review.objects.select_related('customer','provider','service','order')
    qs=_search(qs,request.GET.get('q'),['comment','customer__username','provider__username','service__title','order__order_number'])
    if request.GET.get('public') in {'0','1'}: qs=qs.filter(is_public=request.GET['public']=='1')
    return render(request,'dashboard/reviews/list.html',{**_common(request,'إدارة التقييمات'),'page_obj':_paginate(request,qs.order_by('-created_at'))})
@dashboard_required
@require_POST
def review_action(request, pk, action_name):
    review=get_object_or_404(Review, pk=pk)
    try:
        if action_name=='hide': actions.review_visibility(request,review,False,request.POST.get('reason',''))
        elif action_name=='unhide': actions.review_visibility(request,review,True,request.POST.get('reason',''))
        else: raise ValidationError('إجراء تقييم غير معروف.')
        messages.success(request,'تم تحديث التقييم.')
    except (ValidationError, PermissionDenied) as exc: messages.error(request, exc.messages[0] if hasattr(exc,'messages') else str(exc))
    return redirect('dashboard:reviews')

@dashboard_required
def notifications_list(request):
    qs=Notification.objects.select_related('recipient')
    qs=_search(qs,request.GET.get('q'),['title','message','recipient__username'])
    return render(request,'dashboard/notifications/list.html',{**_common(request,'الإشعارات'),'page_obj':_paginate(request,qs.order_by('-created_at'))})
@dashboard_required
def notification_create(request):
    if request.method=='POST':
        form=NotificationForm(request.POST)
        if form.is_valid():
            target=form.cleaned_data['target']; users=User.objects.none()
            if target=='all': users=User.objects.filter(is_active=True)
            elif target=='customers': users=User.objects.filter(role='customer',is_active=True)
            elif target=='providers': users=User.objects.filter(role='provider',is_active=True)
            elif target=='user': users=User.objects.filter(pk=form.cleaned_data['user'].pk)
            count=0
            for u in users: Notification.objects.create(recipient=u,event_type='admin_message',title=form.cleaned_data['title'],message=form.cleaned_data['message']); count+=1
            actions.audit(request,'notification_sent',None,recipient_scope=target,count=count,title=form.cleaned_data['title']); messages.success(request,f'تم إرسال {count} إشعار.'); return redirect('dashboard:notifications')
    else: form=NotificationForm()
    return render(request,'dashboard/form.html',{**_common(request,'إرسال إشعار'),'form':form,'submit_label':'إرسال'})

@dashboard_required
def terms_view(request):
    if request.method=='POST':
        form=TermsForm(request.POST)
        if form.is_valid(): terms=form.save(); actions.audit(request,'terms_version_created',terms,new={'version':terms.version,'commission_rate':str(terms.commission_rate),'is_active':terms.is_active}); messages.success(request,'تم حفظ نسخة الشروط.'); return redirect('dashboard:settings' if request.path.endswith('/settings/') else 'dashboard:terms')
    else: form=TermsForm()
    return render(request,'dashboard/settings/terms.html',{**_common(request,'الشروط والأحكام'),'terms':TermsAndConditions.objects.order_by('-created_at'),'acceptances':TermsAcceptance.objects.select_related('user','terms').order_by('-accepted_at')[:100],'form':form})

@dashboard_required
def audit_logs(request):
    qs=AuditLog.objects.select_related('actor','content_type')
    qs=_search(qs,request.GET.get('q'),['action','actor__username','object_id'])
    qs=_date_filter(qs,request)
    return render(request,'dashboard/audit/list.html',{**_common(request,'سجل التدقيق'),'page_obj':_paginate(request,qs.order_by('-created_at'))})

@dashboard_required
def reports_view(request, report_type='users'):
    qs_map={'users':User.objects.all(),'providers':ProviderProfile.objects.select_related('user'),'orders':Order.objects.select_related('customer','provider','service'),'payments':Payment.objects.select_related('order'),'commissions':CommissionRecord.objects.select_related('order'),'services':Service.objects.select_related('provider','category'),'reviews':Review.objects.select_related('customer','provider','service')}
    qs=qs_map.get(report_type, User.objects.all()); qs=_date_filter(qs,request)
    return render(request,'dashboard/reports/index.html',{**_common(request,'التقارير'),'report_type':report_type,'page_obj':_paginate(request,qs.order_by('-pk')),'reports':qs_map.keys()})

@dashboard_required
def export_view(request, kind):
    qs_map={'users':User.objects.all(),'providers':ProviderProfile.objects.select_related('user'),'orders':Order.objects.select_related('customer','provider','service'),'payments':Payment.objects.select_related('order'),'commissions':CommissionRecord.objects.select_related('order'),'reviews':Review.objects.select_related('customer','provider','service'),'services':Service.objects.select_related('provider','category')}
    if kind not in EXPORT_MAP or kind not in qs_map: raise Http404('نوع التصدير غير مدعوم')
    filename, fields=EXPORT_MAP[kind]
    actions.audit(request,'csv_export',None,kind=kind)
    return _export_response(filename, _date_filter(qs_map[kind],request), fields)

@dashboard_required
def admin_users(request):
    return render(request,'dashboard/admins/list.html',{**_common(request,'المديرون والصلاحيات'),'admins':User.objects.filter(Q(is_staff=True)|Q(role__in=['admin','super_admin'])),'groups':Group.objects.prefetch_related('permissions').all(),'permissions':Permission.objects.select_related('content_type')[:300]})
@dashboard_required
def group_edit(request, pk=None):
    group=get_object_or_404(Group, pk=pk) if pk else None
    if request.method=='POST':
        form=GroupForm(request.POST, instance=group)
        if form.is_valid(): group=form.save(); actions.audit(request,'admin_group_saved',group); messages.success(request,'تم حفظ الدور/المجموعة.'); return redirect('dashboard:admin_users')
    else: form=GroupForm(instance=group)
    return render(request,'dashboard/form.html',{**_common(request,'إدارة دور إداري'),'form':form,'submit_label':'حفظ الدور'})

def manage_model_page(request, slug, title, model, form_class):
    instance=get_object_or_404(model, pk=request.GET.get('edit')) if request.GET.get('edit') else None
    if request.method=='POST':
        instance=get_object_or_404(model, pk=request.POST.get('pk')) if request.POST.get('pk') else None
        form=form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid(): obj=form.save(); actions.audit(request,f'{slug}_saved',obj); messages.success(request,'تم حفظ البيانات.'); return redirect(f'dashboard:{slug}')
        messages.error(request,'تعذر حفظ البيانات.')
    else: form=form_class(instance=instance)
    qs=model.objects.all()
    if request.GET.get('q') and hasattr(model,'name'): qs=_search(qs,request.GET.get('q'),['name'])
    return render(request,'dashboard/settings/model_list.html',{**_common(request,title),'page_obj':_paginate(request,qs),'form':form,'object_name':title,'edit_obj':instance})

@dashboard_required
def cities(request): return manage_model_page(request,'cities','المدن',City,CityForm)
@dashboard_required
def districts(request): return manage_model_page(request,'districts','المديريات',District,DistrictForm)
@dashboard_required
def managed_services(request): return manage_model_page(request,'managed_services','الخدمات المركزية',ManagedService,ManagedServiceForm)
@dashboard_required
def specializations(request): return manage_model_page(request,'specializations','التخصصات',Specialization,SpecializationForm)
@dashboard_required
def qualifications(request): return manage_model_page(request,'qualifications','المؤهلات',Qualification,QualificationForm)
@dashboard_required
def settings_view(request): return terms_view(request)
