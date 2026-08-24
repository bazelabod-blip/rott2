"""
إشارات تطبيق Reviews
Signals for reviews app - Auto-update ratings
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review


@receiver(post_save, sender=Review)
def update_ratings_on_save(sender, instance, created, **kwargs):
    """
    تحديث متوسط التقييمات عند إنشاء أو تعديل تقييم
    Update average ratings when review is created or updated
    """
    # تحديث متوسط تقييم الخدمة
    service = instance.service
    avg_service_rating = service.reviews.aggregate(
        avg=Avg('service_rating')
    )['avg']
    
    if avg_service_rating is not None:
        service.average_rating = round(avg_service_rating, 2)
    else:
        service.average_rating = 0
    
    service.save(update_fields=['average_rating'])
    
    # تحديث متوسط تقييم مقدم الخدمة
    provider = instance.provider
    if hasattr(provider, 'provider_profile'):
        avg_provider_rating = Review.objects.filter(
            provider=provider
        ).aggregate(avg=Avg('provider_rating'))['avg']
        
        if avg_provider_rating is not None:
            provider.provider_profile.average_rating = round(avg_provider_rating, 2)
        else:
            provider.provider_profile.average_rating = 0
        
        provider.provider_profile.save(update_fields=['average_rating'])


@receiver(post_delete, sender=Review)
def update_ratings_on_delete(sender, instance, **kwargs):
    """
    تحديث متوسط التقييمات عند حذف تقييم
    Update average ratings when review is deleted
    """
    # تحديث متوسط تقييم الخدمة
    service = instance.service
    avg_service_rating = service.reviews.aggregate(
        avg=Avg('service_rating')
    )['avg']
    
    if avg_service_rating is not None:
        service.average_rating = round(avg_service_rating, 2)
    else:
        service.average_rating = 0
    
    service.save(update_fields=['average_rating'])
    
    # تحديث متوسط تقييم مقدم الخدمة
    provider = instance.provider
    if hasattr(provider, 'provider_profile'):
        avg_provider_rating = Review.objects.filter(
            provider=provider
        ).aggregate(avg=Avg('provider_rating'))['avg']
        
        if avg_provider_rating is not None:
            provider.provider_profile.average_rating = round(avg_provider_rating, 2)
        else:
            provider.provider_profile.average_rating = 0
        
        provider.provider_profile.save(update_fields=['average_rating'])
