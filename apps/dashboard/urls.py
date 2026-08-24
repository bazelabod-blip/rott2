from django.urls import path
from . import views
app_name='dashboard'
urlpatterns=[
    path('', views.index, name='index'),
    path('users/', views.users_list, name='users'), path('users/customers/', views.users_list, {'role':'customer'}, name='customers'), path('users/providers/', views.users_list, {'role':'provider'}, name='provider_users'), path('users/create/', views.user_create, name='user_create'), path('users/<int:pk>/', views.user_detail, name='user_detail'), path('users/<int:pk>/edit/', views.user_edit, name='user_edit'), path('users/<int:pk>/<str:action_name>/', views.user_action, name='user_action'), path('users/bulk/', views.users_bulk_action, name='users_bulk'),
    path('providers/', views.providers_list, name='providers'), path('providers/<int:pk>/', views.provider_detail, name='provider_detail'), path('providers/<int:pk>/edit/', views.provider_edit, name='provider_edit'), path('providers/<int:pk>/<str:action_name>/', views.provider_action, name='provider_action'),
    path('verification/', views.verification_list, name='verification'), path('verification/<int:pk>/', views.verification_detail, name='verification_detail'), path('verification/<int:pk>/decision/', views.verification_decision, name='verification_decision'),
    path('documents/', views.documents_list, name='documents'), path('documents/<int:pk>/', views.document_detail, name='document_detail'), path('documents/<int:pk>/review/', views.document_review, name='document_review'), path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('catalog/categories/', views.categories_list, name='categories'), path('catalog/managed-services/', views.managed_services, name='managed_services'), path('catalog/specializations/', views.specializations, name='specializations'), path('catalog/qualifications/', views.qualifications, name='qualifications'),
    path('services/', views.services_list, name='services'), path('services/create/', views.service_edit, name='service_create'), path('services/<int:pk>/edit/', views.service_edit, name='service_edit'), path('services/<int:pk>/<str:action_name>/', views.service_action, name='service_action'),
    path('provider-services/', views.provider_services_list, name='provider_services'), path('provider-services/<int:pk>/<str:action_name>/', views.provider_service_action, name='provider_service_action'),
    path('orders/', views.orders_list, name='orders'), path('orders/<str:order_number>/', views.order_detail, name='order_detail'), path('orders/<str:order_number>/status/', views.order_status_action, name='order_status_action'),
    path('payments/', views.payments_list, name='payments'), path('payments/<int:pk>/', views.payment_detail, name='payment_detail'), path('payments/<int:pk>/<str:action_name>/', views.payment_action, name='payment_action'),
    path('commissions/', views.commissions_list, name='commissions'), path('wallets/', views.wallets_list, name='wallets'), path('reviews/', views.reviews_list, name='reviews'), path('reviews/<int:pk>/<str:action_name>/', views.review_action, name='review_action'),
    path('notifications/', views.notifications_list, name='notifications'), path('notifications/create/', views.notification_create, name='notification_create'),
    path('terms/', views.terms_view, name='terms'), path('locations/cities/', views.cities, name='cities'), path('locations/districts/', views.districts, name='districts'),
    path('reports/', views.reports_view, name='reports'), path('reports/<str:report_type>/', views.reports_view, name='report'), path('export/<str:kind>/', views.export_view, name='export'),
    path('audit/', views.audit_logs, name='audit'), path('admin-users/', views.admin_users, name='admin_users'), path('admin-users/groups/create/', views.group_edit, name='group_create'), path('admin-users/groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('settings/', views.settings_view, name='settings'),
]
