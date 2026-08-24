"""
إعدادات لوحة الإدارة لتطبيق Orders
Admin configuration for orders app
"""
from django.contrib import admin
from .models import Order, Milestone, Delivery, OrderMessage


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """إدارة الطلبات"""
    list_display = [
        'order_number', 'title', 'customer', 'provider',
        'status', 'payment_status', 'agreed_price', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'title', 'customer__username', 'provider__username']
    readonly_fields = [
        'order_number', 'created_at', 'accepted_at', 'started_at',
        'delivered_at', 'completed_at', 'cancelled_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('order_number', 'customer', 'provider', 'service', 'title', 'description')
        }),
        ('التسعير والوقت', {
            'fields': ('agreed_price', 'delivery_days', 'expected_delivery_date')
        }),
        ('الحالة', {
            'fields': ('status', 'payment_status')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'accepted_at', 'started_at', 'delivered_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('الإلغاء', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
    )


"""
@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    # إدراة المعالم (مجمدة مؤقتاً لتجنب تساؤلات المناقشة)
    list_display = ['title', 'order', 'percentage', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['title', 'order__order_number']
    ordering = ['order', 'order_index']
"""


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """إدارة التسليمات"""
    list_display = ['order', 'is_accepted', 'delivered_at', 'reviewed_at']
    list_filter = ['is_accepted', 'delivered_at']
    search_fields = ['order__order_number', 'description']
    readonly_fields = ['delivered_at', 'reviewed_at']
    ordering = ['-delivered_at']


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    """إدارة رسائل الطلبات"""
    list_display = ['order', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['order__order_number', 'sender__username', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
