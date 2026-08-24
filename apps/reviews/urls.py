"""
URLs لتطبيق Reviews
URL routing for reviews app
"""
from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # إنشاء وتعديل تقييم
    path('create/<str:order_number>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_update'),
    
    # تقييمات الخدمة
    path('service/<int:pk>/', views.ServiceReviewsView.as_view(), name='service_reviews'),
    path('provider/<int:pk>/', views.ProviderReviewsView.as_view(), name='provider_reviews'),
]
