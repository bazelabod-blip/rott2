"""
النماذج (Models) لتطبيق Reviews
Models for reviews app - Service and Provider Reviews
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from apps.accounts.models import User
from apps.marketplace.models import Service
from apps.orders.models import Order


class Review(models.Model):
    """
    التقييمات - تقييم الخدمات ومقدميها
    Reviews - Rate services and providers after order completion
    """
    
    # العلاقات
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='الطلب'
    )
    
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        limit_choices_to={'role': 'customer'},
        verbose_name='العميل'
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='الخدمة'
    )
    
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        limit_choices_to={'role': 'provider'},
        verbose_name='مقدم الخدمة'
    )
    
    # التقييمات (1-5 نجوم)
    service_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='تقييم الخدمة',
        help_text='من 1 إلى 5 نجوم'
    )
    
    provider_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='تقييم مقدم الخدمة',
        help_text='من 1 إلى 5 نجوم'
    )
    
    # التعليق
    comment = models.TextField(
        verbose_name='التعليق',
        help_text='شارك تجربتك مع الآخرين'
    )
    
    # الحالة
    is_public = models.BooleanField(
        default=True,
        verbose_name='عام',
        help_text='عرض التقييم للجميع'
    )
    
    # التواريخ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'تقييم'
        verbose_name_plural = 'التقييمات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service', '-created_at']),
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"تقييم {self.customer.username} - {self.service.title}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.order_id:
            if self.order.status != self.order.STATUS_COMPLETED:
                raise ValidationError('لا يمكن التقييم إلا بعد إكمال الطلب.')
            if self.customer_id and self.customer_id != self.order.customer_id:
                raise ValidationError('التقييم مسموح فقط لصاحب الطلب.')
            if self.provider_id and self.provider_id != self.order.provider_id:
                raise ValidationError('مقدم الخدمة يجب أن يطابق الطلب.')

    def get_average_rating(self):
        """حساب متوسط التقييمين"""
        return (self.service_rating + self.provider_rating) / 2
    
    def get_stars_display(self, rating_type='average'):
        """
        الحصول على عرض النجوم بصيغة HTML
        rating_type: 'service', 'provider', or 'average'
        """
        if rating_type == 'service':
            rating = self.service_rating
        elif rating_type == 'provider':
            rating = self.provider_rating
        else:
            rating = self.get_average_rating()
        
        full_stars = int(rating)
        half_star = 1 if (rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars = '⭐' * full_stars
        if half_star:
            stars += '½⭐'
        stars += '☆' * empty_stars
        
        return stars
    
    def get_absolute_url(self):
        """رابط صفحة التقييم"""
        return reverse('reviews:review_detail', kwargs={'pk': self.pk})
    
    @property
    def can_be_edited(self):
        """هل يمكن تعديل التقييم؟"""
        # يمكن التعديل في أي وقت (لا قيود زمنية)
        return True
    
    @property
    def rating_color(self):
        """لون حسب متوسط التقييم"""
        avg = self.get_average_rating()
        if avg >= 4.5:
            return 'success'
        elif avg >= 3.5:
            return 'primary'
        elif avg >= 2.5:
            return 'warning'
        else:
            return 'danger'
