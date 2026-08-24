"""
إعدادات لوحة الإدارة لتطبيق Reviews
Admin configuration for reviews app
"""
from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """إدارة التقييمات"""
    list_display = [
        'customer', 'service', 'provider',
        'service_rating', 'provider_rating', 'get_average_rating',
        'is_public', 'created_at'
    ]
    list_filter = ['service_rating', 'provider_rating', 'is_public', 'created_at']
    search_fields = [
        'customer__username', 'service__title',
        'provider__username', 'comment'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('معلومات التقييم', {
            'fields': ('order', 'customer', 'service', 'provider')
        }),
        ('التقييمات', {
            'fields': ('service_rating', 'provider_rating')
        }),
        ('التعليق', {
            'fields': ('comment', 'is_public')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_average_rating(self, obj):
        """عرض متوسط التقييم"""
        return f"{obj.get_average_rating():.1f}"
    get_average_rating.short_description = 'المتوسط'
