"""
النماذج (Forms) لتطبيق Marketplace  
Forms for marketplace app
"""
from django import forms
from .models import Category, Service


class ServiceForm(forms.ModelForm):
    """
    نموذج إضافة/تعديل خدمة
    Service create/update form
    """
    
    class Meta:
        model = Service
        fields = [
            'title', 'category', 'description',
            'price_type', 'currency', 'price', 'delivery_time',
            'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: تصميم شعار احترافي'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'اشرح تفاصيل الخدمة، ماذا ستقدم، المتطلبات، إلخ...'
            }),
            'price_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'delivery_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'عدد الأيام',
                'min': '1'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان الخدمة',
            'category': 'التصنيف',
            'description': 'وصف الخدمة',
            'price_type': 'نوع السعر',
            'currency': 'العملة',
            'price': 'السعر',
            'delivery_time': 'مدة التسليم (بالأيام)',
            'image': 'صورة الخدمة',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # عرض التصنيفات النشطة فقط
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        price_type = cleaned_data.get('price_type')
        price = cleaned_data.get('price')
        
        # التحقق من وجود السعر إذا كان النوع ليس "قابل للتفاوض"
        if price_type in ['fixed', 'hourly'] and not price:
            raise forms.ValidationError(
                'يجب تحديد السعر عند اختيار "سعر ثابت" أو "بالساعة"'
            )
        
        return cleaned_data


class ServiceSearchForm(forms.Form):
    """
    نموذج البحث والفلترة
    Search and filter form
    """
    
    SORT_CHOICES = [
        ('-created_at', 'الأحدث'),
        ('-orders_count', 'الأكثر طلباً'),
        ('-average_rating', 'الأعلى تقييماً'),
        ('price', 'الأقل سعراً'),
        ('-price', 'الأعلى سعراً'),
    ]
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث عن خدمة...',
            'autocomplete': 'off',
            'value': '',
        }),
        label='البحث'
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='جميع التصنيفات',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='التصنيف'
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'من',
            'step': '0.01',
            'value': '',
        }),
        label='السعر الأدنى'
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'إلى',
            'step': '0.01',
            'value': '',
        }),
        label='السعر الأعلى'
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='ترتيب حسب'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تفريغ القيم الأولية لمنع تعبئة الخانات بعد البحث
        for field in self.fields.values():
            field.initial = None
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(
                'السعر الأدنى يجب أن يكون أقل من السعر الأعلى'
            )
        
        return cleaned_data