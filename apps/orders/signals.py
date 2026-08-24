"""
إشارات تطبيق Orders
Signals for orders app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def update_service_order_count(sender, instance, created, **kwargs):
    """
    تحديث عدد الطلبات للخدمة عند إنشاء طلب جديد
    Update service order count when order is created
    """
    if created and instance.service:
        # زيادة عداد الطلبات
        instance.service.orders_count += 1
        instance.service.save(update_fields=['orders_count'])


@receiver(post_save, sender=Order)
def handle_order_status_changes(sender, instance, created, **kwargs):
    """
    معالجة تغييرات حالة الطلب
    Handle order status changes
    """
    if not created:
        # يمكن إضافة منطق إضافي هنا مثل:
        # - إرسال إشعارات
        # - تحديث إحصائيات المستخدم
        # - إرسال بريد إلكتروني
        pass
