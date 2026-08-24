"""
Views لتطبيق Reviews
Views for reviews app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from .models import Review
from .forms import ReviewForm
from apps.orders.models import Order
from apps.marketplace.models import Service
from apps.accounts.models import User


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """
    إنشاء تقييم جديد (Customers only, after order completion)
    """
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        # الحصول على الطلب
        self.order = get_object_or_404(Order, order_number=kwargs['order_number'])
        
        # التحقق من أن المستخدم customer
        if not request.user.is_customer():
            messages.error(request, 'التقييم متاح للعملاء فقط.')
            return redirect('orders:order_detail', order_number=self.order.order_number)
        
        # التحقق من أن المستخدم هو صاحب الطلب
        if self.order.customer != request.user:
            messages.error(request, 'ليس لديك صلاحية لتقييم هذا الطلب.')
            return redirect('home')
        
        # التحقق من إكمال الطلب
        if self.order.status != 'completed':
            messages.error(request, 'يمكنك التقييم فقط بعد إكمال الطلب.')
            return redirect('orders:order_detail', order_number=self.order.order_number)
        
        # التحقق من عدم وجود تقييم سابق
        if hasattr(self.order, 'review'):
            messages.warning(request, 'لقد قمت بتقييم هذا الطلب مسبقاً.')
            return redirect('reviews:review_update', pk=self.order.review.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        review = form.save(commit=False)
        review.order = self.order
        review.customer = self.request.user
        review.service = self.order.service
        review.provider = self.order.provider
        review.save()
        
        messages.success(self.request, 'شكراً لك! تم إضافة تقييمك بنجاح.')
        return redirect('orders:order_detail', order_number=self.order.order_number)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context


class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    تعديل تقييم (Owner only)
    """
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_update.html'
    
    def test_func(self):
        review = self.get_object()
        return self.request.user == review.customer
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث تقييمك بنجاح.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('orders:order_detail', kwargs={'order_number': self.object.order.order_number})


class ServiceReviewsView(ListView):
    """
    عرض جميع تقييمات خدمة معينة
    """
    model = Review
    template_name = 'reviews/service_reviews_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        self.service = get_object_or_404(Service, pk=self.kwargs['pk'])
        return Review.objects.filter(
            service=self.service,
            is_public=True
        ).select_related('customer', 'order').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        
        # إحصائيات التقييمات
        reviews = self.get_queryset()
        total = reviews.count()
        
        if total > 0:
            # توزيع التقييمات
            context['rating_distribution'] = {
                5: reviews.filter(service_rating=5).count(),
                4: reviews.filter(service_rating=4).count(),
                3: reviews.filter(service_rating=3).count(),
                2: reviews.filter(service_rating=2).count(),
                1: reviews.filter(service_rating=1).count(),
            }
            context['total_reviews'] = total
        
        return context


class ProviderReviewsView(ListView):
    """
    عرض جميع تقييمات مقدم خدمة معين
    """
    model = Review
    template_name = 'reviews/provider_reviews_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        self.provider = get_object_or_404(User, pk=self.kwargs['pk'], role='provider')
        return Review.objects.filter(
            provider=self.provider,
            is_public=True
        ).select_related('customer', 'service', 'order').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provider'] = self.provider
        
        # إحصائيات التقييمات
        reviews = self.get_queryset()
        total = reviews.count()
        
        if total > 0:
            # توزيع التقييمات
            context['rating_distribution'] = {
                5: reviews.filter(provider_rating=5).count(),
                4: reviews.filter(provider_rating=4).count(),
                3: reviews.filter(provider_rating=3).count(),
                2: reviews.filter(provider_rating=2).count(),
                1: reviews.filter(provider_rating=1).count(),
            }
            context['total_reviews'] = total
        
        return context
