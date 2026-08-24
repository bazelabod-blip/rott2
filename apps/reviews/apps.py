"""
تكوين تطبيق Reviews
Reviews app configuration
"""
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'
    verbose_name = 'التقييمات والمراجعات'
    
    def ready(self):
        """استيراد الإشارات عند تشغيل التطبيق"""
        import apps.reviews.signals
