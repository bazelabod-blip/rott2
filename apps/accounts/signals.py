"""
إشارات (Signals) لإنشاء ملف مقدم الخدمة تلقائياً
Signals to auto-create provider profile
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, ProviderProfile


@receiver(post_save, sender=User)
def create_provider_profile(sender, instance, created, **kwargs):
    """
    إنشاء ملف مقدم خدمة تلقائياً عند إنشاء مستخدم بدور provider
    Auto-create provider profile when user with provider role is created
    """
    if created and instance.role == 'provider':
        ProviderProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_provider_profile(sender, instance, **kwargs):
    """
    حفظ ملف مقدم الخدمة عند حفظ المستخدم
    Save provider profile when user is saved
    """
    if instance.role == 'provider':
        if not hasattr(instance, 'provider_profile'):
            ProviderProfile.objects.create(user=instance)
