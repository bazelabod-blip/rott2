"""
النماذج (Models) لتطبيق Orders
Models for orders app - Orders, Milestones, Deliveries, Messages
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from apps.accounts.models import User
from apps.marketplace.models import Service
import uuid
from datetime import timedelta


class Order(models.Model):
    """
    الطلبات - العقود بين العملاء ومقدمي الخدمات
    Orders - Contracts between customers and providers
    """
    
    STATUS_PENDING='pending'; STATUS_ACCEPTED='accepted'; STATUS_PAYMENT_PENDING='payment_pending'; STATUS_PAID='paid'; STATUS_IN_PROGRESS='in_progress'; STATUS_DELIVERED='delivered'; STATUS_COMPLETED='completed'; STATUS_REJECTED='rejected'; STATUS_CANCELLED='cancelled'; STATUS_DISPUTED='disputed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'في انتظار الموافقة'),
        (STATUS_ACCEPTED, 'مقبول'),
        (STATUS_PAYMENT_PENDING, 'بانتظار الدفع'),
        (STATUS_PAID, 'مدفوع'),
        (STATUS_IN_PROGRESS, 'قيد التنفيذ'),
        (STATUS_DELIVERED, 'تم التسليم'),
        (STATUS_COMPLETED, 'مكتمل'),
        (STATUS_REJECTED, 'مرفوض'),
        (STATUS_CANCELLED, 'ملغي'),
        (STATUS_DISPUTED, 'متنازع عليه'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('paid', 'مدفوع'),
        ('failed', 'فشل'),
        ('refunded', 'مسترد'),
        ('cancelled', 'ملغي'),
    ]
    
    # العلاقات
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_customer',
        limit_choices_to={'role': 'customer'},
        verbose_name='العميل'
    )
    
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_provider',
        limit_choices_to={'role': 'provider'},
        verbose_name='مقدم الخدمة'
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name='الخدمة'
    )
    
    # المعلومات الأساسية
    order_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='رقم الطلب'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الطلب'
    )
    
    description = models.TextField(
        verbose_name='تفاصيل ومتطلبات الطلب',
        help_text='اشرح ما تريده بالتفصيل'
    )
    
    # التسعير والوقت
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='السعر المتفق عليه (ريال)'
    )
    
    delivery_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='مدة التسليم (بالأيام)'
    )
    
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التسليم المتوقع'
    )
    
    # الحالات
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الطلب'
    )
    
    currency = models.CharField(max_length=3, default='YER', verbose_name='العملة')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    provider_net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الدفع'
    )
    
    # التواريخ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ القبول'
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ البدء'
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التسليم'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال'
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإلغاء'
    )
    
    dispute_reason = models.TextField(blank=True, verbose_name='سبب النزاع')
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name='سبب الإلغاء'
    )
    
    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        """توليد رقم طلب فريد تلقائياً"""
        if not self.order_number:
            # تنسيق: ORD-2024-XXXXX
            year = timezone.now().year
            random_part = str(uuid.uuid4().int)[:5]
            self.order_number = f"ORD-{year}-{random_part}"
            
            # التأكد من أن الرقم فريد
            while Order.objects.filter(order_number=self.order_number).exists():
                random_part = str(uuid.uuid4().int)[:5]
                self.order_number = f"ORD-{year}-{random_part}"
        
        # حساب تاريخ التسليم المتوقع
        if not self.expected_delivery_date and self.accepted_at and self.delivery_days:
            self.expected_delivery_date = (self.accepted_at + timedelta(days=self.delivery_days)).date()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """رابط صفحة الطلب"""
        return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
    
    ALLOWED_TRANSITIONS={STATUS_PENDING:{STATUS_ACCEPTED,STATUS_REJECTED,STATUS_CANCELLED},STATUS_ACCEPTED:{STATUS_PAYMENT_PENDING,STATUS_CANCELLED},STATUS_PAYMENT_PENDING:{STATUS_PAID,STATUS_CANCELLED},STATUS_PAID:{STATUS_IN_PROGRESS,STATUS_DISPUTED},STATUS_IN_PROGRESS:{STATUS_DELIVERED,STATUS_DISPUTED},STATUS_DELIVERED:{STATUS_COMPLETED,STATUS_DISPUTED}}
    def can_transition_to(self, new_status): return new_status in self.ALLOWED_TRANSITIONS.get(self.status,set())
    def transition_to(self, new_status, actor=None):
        from django.core.exceptions import ValidationError
        if not self.can_transition_to(new_status): raise ValidationError(f'Invalid order transition {self.status} -> {new_status}')
        self.status=new_status
        now=timezone.now()
        if new_status==self.STATUS_ACCEPTED: self.accepted_at=now
        elif new_status==self.STATUS_IN_PROGRESS: self.started_at=now
        elif new_status==self.STATUS_DELIVERED: self.delivered_at=now
        elif new_status==self.STATUS_COMPLETED: self.completed_at=now
        elif new_status in [self.STATUS_CANCELLED,self.STATUS_REJECTED]: self.cancelled_at=now
    def can_be_cancelled(self):
        """هل يمكن إلغاء الطلب؟"""
        return self.status in [self.STATUS_PENDING, self.STATUS_ACCEPTED, self.STATUS_PAYMENT_PENDING]
    
    def can_be_accepted(self):
        """هل يمكن قبول الطلب؟"""
        return self.status == self.STATUS_PENDING
    
    def can_be_started(self):
        """هل يمكن بدء العمل؟"""
        return self.status == self.STATUS_PAID
    
    def can_be_delivered(self):
        """هل يمكن التسليم؟"""
        return self.status == self.STATUS_IN_PROGRESS
    
    def can_be_completed(self):
        """هل يمكن إكمال الطلب؟"""
        return self.status == self.STATUS_DELIVERED
    
    def is_active(self):
        """هل الطلب نشط (غير منتهي)؟"""
        return self.status not in [self.STATUS_COMPLETED, self.STATUS_CANCELLED, self.STATUS_DISPUTED]
    
    def get_status_badge_class(self):
        """الحصول على class للـ badge حسب الحالة"""
        status_classes = {
            'pending': 'bg-warning',
            'accepted': 'bg-info',
            'in_progress': 'bg-primary',
            'delivered': 'bg-success',
            'completed': 'bg-success',
            'cancelled': 'bg-secondary',
            'disputed': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_payment_badge_class(self):
        """الحصول على class للـ badge حسب حالة الدفع"""
        payment_classes = {
            'pending': 'bg-warning',
            'paid': 'bg-success',
            'refunded': 'bg-secondary',
        }
        return payment_classes.get(self.payment_status, 'bg-secondary')


class Milestone(models.Model):
    """
    معالم المشروع - تقسيم العمل لمراحل
    Project milestones
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='الطلب'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان المرحلة'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name='نسبة الإنجاز (%)'
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name='مكتملة'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال'
    )
    
    order_index = models.IntegerField(
        default=0,
        verbose_name='الترتيب'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'معلم'
        verbose_name_plural = 'المعالم'
        ordering = ['order', 'order_index']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.title}"


class Delivery(models.Model):
    """
    التسليمات - الملفات والأعمال المسلمة
    Deliverables - Files and work delivered
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='الطلب'
    )
    
    file = models.FileField(
        upload_to='deliveries/%Y/%m/',
        verbose_name='ملف التسليم'
    )
    
    description = models.TextField(
        verbose_name='وصف التسليم',
        help_text='اشرح ما تم إنجازه'
    )
    
    delivered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التسليم'
    )
    
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='مقبول'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ المراجعة'
    )
    
    review_note = models.TextField(
        blank=True,
        verbose_name='ملاحظات المراجعة'
    )
    
    class Meta:
        verbose_name = 'تسليم'
        verbose_name_plural = 'التسليمات'
        ordering = ['-delivered_at']
    
    def __str__(self):
        return f"تسليم - {self.order.order_number}"


class OrderMessage(models.Model):
    """
    رسائل الطلب - التواصل بين العميل والمقدم حول الطلب
    Order messages - Communication about the order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='الطلب'
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='order_messages',
        verbose_name='المرسل'
    )
    
    message = models.TextField(
        verbose_name='الرسالة'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإرسال'
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name='مقروءة'
    )
    
    class Meta:
        verbose_name = 'رسالة طلب'
        verbose_name_plural = 'رسائل الطلبات'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.order.order_number}"
