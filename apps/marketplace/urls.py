"""
URLs لتطبيق Marketplace
URL routing for marketplace app
"""
from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    # روابط الخدمة
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('search/', views.GlobalSearchView.as_view(), name='global_search'),
    path('providers/', views.ProviderSearchView.as_view(), name='provider_search'),
    path('services/add/', views.ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('services/<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),

    
    # خدمات المقدم
    path('my-services/', views.my_services_view, name='my_services'),
    
    # روابط التصنيفات
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
]
