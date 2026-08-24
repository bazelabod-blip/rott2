"""
تكوين تطبيق Orders
Orders app configuration
"""
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'الطلبات والعقود'
    
    def ready(self):
        """استيراد الإشارات عند تشغيل التطبيق"""
        import apps.orders.signals
