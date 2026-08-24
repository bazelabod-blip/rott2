"""
Forms for Chat app
"""
from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    """نموذج إرسال رسالة"""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'اكتب رسالتك هنا...',
                'style': 'resize: none;'
            })
        }
        labels = {
            'content': ''
        }
