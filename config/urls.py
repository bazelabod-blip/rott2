"""
ملف URLs الرئيسي لمشروع منصة سوق الخدمات
URL Configuration for service_marketplace project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.marketplace.views import home_view
from apps.core.admin_dashboard import install_admin_dashboard
install_admin_dashboard()

urlpatterns = [
    # لوحة تحكم Django الإدارية
    path('admin/', admin.site.urls),
    path('dashboard/', include('apps.dashboard.urls')),
    
    # الصفحة الرئيسية
    path('', home_view, name='home'),
    
    # روابط التطبيقات
    path('accounts/', include('apps.accounts.urls')),
    path('marketplace/', include('apps.marketplace.urls')),
    path('orders/', include('apps.orders.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('chat/', include('apps.chat.urls')),
    path('payments/', include('apps.payments.urls')),
]

# إضافة روابط الوسائط في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
