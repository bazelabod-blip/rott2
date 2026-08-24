"""
النماذج (Forms) لتطبيق Reviews
Forms for reviews app
"""
from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """
    نموذج إنشاء/تعديل تقييم
    Review creation/update form
    """
    
    class Meta:
        model = Review
        fields = ['service_rating', 'provider_rating', 'comment', 'is_public']
        widgets = {
            'service_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '1',
                'placeholder': '5'
            }),
            'provider_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '1',
                'placeholder': '5'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'شارك تجربتك مع الخدمة ومقدمها...'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'service_rating': 'تقييم الخدمة (1-5 نجوم)',
            'provider_rating': 'تقييم مقدم الخدمة (1-5 نجوم)',
            'comment': 'تعليقك',
            'is_public': 'جعل التقييم عاماً',
        }
        help_texts = {
            'service_rating': 'قيّم جودة الخدمة المقدمة',
            'provider_rating': 'قيّم احترافية وتعامل مقدم الخدمة',
            'comment': 'اكتب تجربتك بالتفصيل لمساعدة الآخرين',
        }
    
    def clean_service_rating(self):
        """التحقق من صحة تقييم الخدمة"""
        rating = self.cleaned_data.get('service_rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError('يجب أن يكون التقييم بين 1 و 5')
        return rating
    
    def clean_provider_rating(self):
        """التحقق من صحة تقييم المقدم"""
        rating = self.cleaned_data.get('provider_rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError('يجب أن يكون التقييم بين 1 و 5')
        return rating
    
    def clean_comment(self):
        """التحقق من التعليق"""
        comment = self.cleaned_data.get('comment')
        if len(comment) < 10:
            raise forms.ValidationError('يجب أن يكون التعليق 10 أحرف على الأقل')
        return comment
