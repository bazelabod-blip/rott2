"""
ملف إعدادات تطبيق accounts
Configuration for accounts app
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'إدارة المستخدمين'
    
    def ready(self):
        """يتم تنفيذها عند بدء التطبيق - لتحميل الـ signals"""
        import apps.accounts.signals
