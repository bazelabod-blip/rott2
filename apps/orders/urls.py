"""
URLs لتطبيق Orders
URL routing for orders app
"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # قوائم الطلبات
    path('', views.OrderListView.as_view(), name='order_list'),
    path('provider/', views.ProviderOrdersView.as_view(), name='provider_orders'),
    
    # إنشاء طلب
    path('create/<int:service_id>/', views.OrderCreateView.as_view(), name='order_create'),
    
    # تفاصيل الطلب
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # إجراءات الطلب
    path('<str:order_number>/accept/', views.order_accept, name='order_accept'),
    path('<str:order_number>/reject/', views.order_reject, name='order_reject'),
    path('<str:order_number>/start/', views.order_start, name='order_start'),
    path('<str:order_number>/deliver/', views.order_deliver, name='order_deliver'),
    path('<str:order_number>/complete/', views.order_complete, name='order_complete'),
    path('<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),
    
    # رسائل
    path('<str:order_number>/message/', views.send_order_message, name='send_message'),
]
