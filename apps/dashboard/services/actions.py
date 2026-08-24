from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import ProviderDocument, ProviderProfile, ProviderVerificationRequest, User
from apps.core.models import AuditLog, Notification
from apps.marketplace.models import Service, ProviderService
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import mark_payment_failed
from apps.reviews.models import Review


def client_ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0]


def audit(request, action, target=None, **metadata):
    metadata.setdefault('ip', client_ip(request))
    ct = ContentType.objects.get_for_model(target) if target is not None else None
    return AuditLog.objects.create(actor=request.user, action=action, content_type=ct, object_id=str(getattr(target, 'pk', '')) if target is not None else '', metadata=metadata)


def notify(user, event_type, title, message):
    if user and user.is_active:
        return Notification.objects.create(recipient=user, event_type=event_type, title=title, message=message)


def require_perm(user, perm):
    if user.is_superuser or user.has_perm(perm):
        return True
    if getattr(user, 'role', '') == 'super_admin':
        return True
    raise PermissionDenied('ليست لديك صلاحية تنفيذ هذا الإجراء.')

@transaction.atomic
def update_user_status(request, user, action, reason=''):
    if user == request.user and action in {'deactivate','suspend'}:
        raise ValidationError('لا يمكنك تعطيل حسابك الحالي.')
    old = {'is_active': user.is_active, 'role': user.role}
    if action in {'activate','restore'}: user.is_active = True
    elif action in {'deactivate','suspend'}: user.is_active = False
    else: raise ValidationError('إجراء مستخدم غير معروف.')
    user.save(update_fields=['is_active','updated_at'])
    audit(request, f'user_{action}', user, old=old, new={'is_active': user.is_active}, reason=reason)
    notify(user, 'account_status_changed', 'تحديث حالة الحساب', f'تم تحديث حالة حسابك بواسطة الإدارة. {reason}')
    return user

@transaction.atomic
def change_user_role(request, user, role, reason=''):
    if role not in dict(User.ROLE_CHOICES): raise ValidationError('الدور غير صالح.')
    old = user.role; user.role = role; user.save(update_fields=['role','updated_at'])
    audit(request, 'user_role_changed', user, old={'role': old}, new={'role': role}, reason=reason)
    notify(user, 'account_status_changed', 'تحديث دور الحساب', f'تم تغيير دور حسابك إلى {user.get_role_display()}.')
    return user

@transaction.atomic
def provider_action(request, provider, action, reason=''):
    old = {'status': provider.status, 'verification_status': provider.verification_status}
    if action == 'verify':
        provider.status='active'; provider.verification_status='verified'; provider.verified_by=request.user; provider.verified_at=timezone.now()
        event='provider_verified'; title='تم توثيق حسابك'
    elif action == 'reject':
        if not reason: raise ValidationError('سبب الرفض مطلوب.')
        provider.status='inactive'; provider.verification_status='rejected'; event='provider_rejected'; title='تم رفض التوثيق'
    elif action == 'request_documents':
        if not reason: raise ValidationError('ملاحظة المستندات مطلوبة.')
        provider.status='inactive'; provider.verification_status='needs_documents'; event='documents_requested'; title='مطلوب مستندات إضافية'
    elif action == 'suspend':
        provider.status='suspended'; provider.verification_status='suspended'; event='provider_rejected'; title='تم إيقاف حساب مقدم الخدمة'
    elif action in {'activate','restore','unsuspend'}:
        provider.status='active'; event='provider_verified'; title='تم تفعيل حساب مقدم الخدمة'
    elif action == 'deactivate':
        provider.status='inactive'; event='provider_rejected'; title='تم تعطيل حساب مقدم الخدمة'
    else: raise ValidationError('إجراء مقدم الخدمة غير معروف.')
    provider.admin_notes = reason or provider.admin_notes
    provider.save()
    audit(request, f'provider_{action}', provider, old=old, new={'status':provider.status,'verification_status':provider.verification_status}, reason=reason)
    notify(provider.user, event, title, reason or 'تم تحديث حالة ملفك بواسطة الإدارة.')
    return provider

@transaction.atomic
def verification_action(request, verification, status, note=''):
    old = verification.status
    verification.status=status; verification.admin_note=note; verification.reviewed_by=request.user; verification.reviewed_at=timezone.now(); verification.save()
    map_action={'approved':'verify','rejected':'reject','needs_documents':'request_documents','on_hold':'deactivate','pending':'deactivate'}
    if status in map_action: provider_action(request, verification.provider, map_action[status], note)
    if status == 'approved':
        for managed in verification.requested_services.filter(is_active=True):
            ProviderService.objects.update_or_create(provider=verification.provider, catalog_service=managed, defaults={'price':0,'is_active':True,'approval_status':'active'})
    audit(request, 'verification_decision', verification, old={'status':old}, new={'status':status}, reason=note)
    return verification

@transaction.atomic
def document_action(request, document, action, note=''):
    old = document.status
    if action not in dict(ProviderDocument.STATUS_CHOICES): raise ValidationError('إجراء مستند غير صالح.')
    if action in {'rejected','needs_additional_documents'} and not note: raise ValidationError('الملاحظة مطلوبة لهذا الإجراء.')
    document.status=action; document.review_note=note; document.reviewed_by=request.user; document.reviewed_at=timezone.now(); document.save()
    audit(request, f'document_{action}', document, old={'status':old}, new={'status':document.status}, reason=note)
    notify(document.provider.user, 'documents_requested' if action!='approved' else 'provider_submitted', 'تحديث مستندات التوثيق', note or f'تم تحديث حالة مستند {document.document_type.name}.')
    return document

@transaction.atomic
def service_action(request, obj, action, reason=''):
    old = {'status': getattr(obj,'status', None), 'is_active': getattr(obj,'is_active', None), 'approval_status': getattr(obj,'approval_status', None)}
    if isinstance(obj, Service):
        if action in {'activate','publish'}: obj.status='active'
        elif action in {'deactivate','unpublish'}: obj.status='paused'
        elif action == 'close': obj.status='closed'
        else: raise ValidationError('إجراء خدمة غير صالح.')
        obj.save(update_fields=['status','updated_at'])
    elif isinstance(obj, ProviderService):
        if action in {'approve','activate'}: obj.approval_status='active'; obj.is_active=True
        elif action == 'deactivate': obj.is_active=False
        elif action == 'reject': obj.approval_status='rejected'; obj.is_active=False
        else: raise ValidationError('إجراء خدمة مقدم غير صالح.')
        obj.save()
    audit(request, f'{obj.__class__.__name__.lower()}_{action}', obj, old=old, new={'status':getattr(obj,'status',None),'is_active':getattr(obj,'is_active',None),'approval_status':getattr(obj,'approval_status',None)}, reason=reason)
    return obj

@transaction.atomic
def change_order_status(request, order, new_status, reason='', force=False):
    old = order.status
    if not force:
        order.transition_to(new_status, actor=request.user)
    else:
        if new_status not in dict(Order.STATUS_CHOICES): raise ValidationError('حالة الطلب غير صالحة.')
        order.status = new_status
    if new_status == Order.STATUS_CANCELLED and reason: order.cancellation_reason = reason
    if new_status == Order.STATUS_DISPUTED and reason: order.dispute_reason = reason
    order.save()
    audit(request, 'order_status_changed', order, old={'status':old}, new={'status':order.status}, reason=reason, force=force)
    notify(order.customer, 'order_completed' if new_status==Order.STATUS_COMPLETED else 'order_started', 'تحديث حالة الطلب', f'تم تحديث الطلب {order.order_number} إلى {order.get_status_display()}.')
    notify(order.provider, 'order_completed' if new_status==Order.STATUS_COMPLETED else 'order_started', 'تحديث حالة الطلب', f'تم تحديث الطلب {order.order_number} إلى {order.get_status_display()}.')
    return order

@transaction.atomic
def payment_refund(request, payment, reason=''):
    if payment.status != Payment.STATUS_PAID: raise ValidationError('لا يمكن استرداد دفعة غير مدفوعة.')
    old = payment.status; payment.status=Payment.STATUS_REFUNDED; payment.reviewed_by=request.user; payment.reviewed_at=timezone.now(); payment.review_note=reason; payment.save()
    payment.order.payment_status='refunded'; payment.order.save(update_fields=['payment_status'])
    audit(request, 'payment_refunded_internal', payment, old={'status':old}, new={'status':payment.status}, reason=reason, note='استرداد داخلي فقط؛ لا توجد بوابة خارجية.')
    notify(payment.order.customer, 'payment_failed', 'تم تسجيل استرداد الدفع', reason or f'تم تسجيل استرداد للطلب {payment.order.order_number}.')
    return payment

@transaction.atomic
def review_visibility(request, review, visible, reason=''):
    old = review.is_public; review.is_public = visible; review.save(update_fields=['is_public','updated_at'])
    audit(request, 'review_visibility_changed', review, old={'is_public':old}, new={'is_public':visible}, reason=reason)
    return review
