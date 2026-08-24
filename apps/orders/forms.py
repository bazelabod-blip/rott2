"""
النماذج (Forms) لتطبيق Orders
Forms for orders app
"""
from django import forms
from .models import Order, Delivery, Milestone, OrderMessage


class OrderCreateForm(forms.ModelForm):
    """
    نموذج إنشاء طلب جديد
    Create new order form
    """
    
    class Meta:
        model = Order
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'اشرح متطلباتك بالتفصيل...'
            }),
        }
        labels = {
            'description': 'تفاصيل ومتطلبات الطلب',
        }


class DeliveryForm(forms.ModelForm):
    """
    نموذج رفع ملفات التسليم
    Delivery upload form
    """
    
    class Meta:
        model = Delivery
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'اشرح ما تم إنجازه...'
            }),
        }
        labels = {
            'file': 'ملف التسليم',
            'description': 'وصف التسليم',
        }


class MilestoneForm(forms.ModelForm):
    """
    نموذج إضافة معلم
    Milestone form
    """
    
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'percentage']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: المرحلة الأولى - التصميم'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': '25'
            }),
        }
        labels = {
            'title': 'عنوان المرحلة',
            'description': 'الوصف',
            'percentage': 'نسبة الإنجاز (%)',
        }


class OrderMessageForm(forms.ModelForm):
    """
    نموذج إرسال رسالة حول الطلب
    Order message form
    """
    
    class Meta:
        model = OrderMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'اكتب رسالتك هنا...'
            }),
        }
        labels = {
            'message': 'الرسالة',
        }


class CancellationForm(forms.Form):
    """
    نموذج إلغاء الطلب
    Cancellation form
    """
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'اشرح سبب الإلغاء...'
        }),
        label='سبب الإلغاء',
        required=True
    )
