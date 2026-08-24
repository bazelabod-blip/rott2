"""
منطق الأعمال لتطبيق accounts
Business logic for accounts app
"""
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from .models import User, ProviderProfile


def register_user(username, email, password, role='customer', **extra_fields):
    """
    تسجيل مستخدم جديد
    Register a new user
    
    Args:
        username: اسم المستخدم
        email: البريد الإلكتروني
        password: كلمة المرور
        role: الدور (customer/provider)
        **extra_fields: حقول إضافية (phone, city)
    
    Returns:
        User object
    """
    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            **extra_fields
        )
        
        # الـ Signal سيقوم بإنشاء ProviderProfile تلقائياً إن كان provider
        return user


def authenticate_user(request, username, password):
    """
    مصادقة وتسجيل دخول المستخدم
    Authenticate and login user
    
    Returns:
        User object if successful, None otherwise
    """
    user = authenticate(request, username=username, password=password)
    if user is not None and user.is_active:
        login(request, user)
        return user
    return None


def logout_user(request):
    """
    تسجيل خروج المستخدم
    Logout user
    """
    logout(request)


def update_user_profile(user, **fields):
    """
    تحديث معلومات المستخدم الأساسية
    Update user basic info
    """
    for field, value in fields.items():
        if hasattr(user, field):
            setattr(user, field, value)
    user.save()
    return user


def update_provider_profile(provider_profile, **fields):
    """
    تحديث ملف مقدم الخدمة
    Update provider profile
    """
    for field, value in fields.items():
        if hasattr(provider_profile, field):
            setattr(provider_profile, field, value)
    provider_profile.save()
    return provider_profile


def get_provider_profile(user):
    """
    الحصول على ملف مقدم الخدمة أو إنشاءه
    Get or create provider profile
    """
    if user.role == 'provider':
        profile, created = ProviderProfile.objects.get_or_create(user=user)
        return profile
    return None


def calculate_provider_rating(provider_profile):
    """
    حساب متوسط تقييم مقدم الخدمة
    Calculate provider average rating (will be used later with reviews)
    """
    # سيتم استخدامها في المرحلة 6 (التقييمات)
    pass
