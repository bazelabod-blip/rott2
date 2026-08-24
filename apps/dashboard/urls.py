from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('users/', views.users_list, name='users'), path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('providers/', views.providers_list, name='providers'), path('providers/<int:pk>/', views.provider_detail, name='provider_detail'),
    path('verification/', views.verification_list, name='verification'), path('verification/<int:pk>/', views.verification_detail, name='verification_detail'), path('verification/<int:pk>/decision/', views.verification_decision, name='verification_decision'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('services/', views.services_list, name='services'), path('orders/', views.orders_list, name='orders'), path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('payments/', views.payments_list, name='payments'), path('commissions/', views.commissions_list, name='commissions'), path('wallets/', views.wallets_list, name='wallets'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('locations/cities/', views.manage_model_list('cities', 'المدن', views.City, views.CityForm), name='cities'),
    path('locations/districts/', views.manage_model_list('districts', 'المديريات', views.District, views.DistrictForm), name='districts'),
    path('catalog/managed-services/', views.manage_model_list('managed_services', 'الخدمات المركزية', views.ManagedService, views.ManagedServiceForm), name='managed_services'),
    path('catalog/specializations/', views.manage_model_list('specializations', 'التخصصات', views.Specialization, views.SpecializationForm), name='specializations'),
    path('catalog/qualifications/', views.manage_model_list('qualifications', 'المؤهلات', views.Qualification, views.QualificationForm), name='qualifications'),
    path('settings/', views.settings_view, name='settings'),
]
