from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.forms import SetPasswordForm
from apps.accounts.models import ProviderProfile, ProviderDocument, ProviderVerificationRequest
from apps.core.models import City, District, TermsAndConditions, Notification
from apps.marketplace.models import Category, Service, ManagedService, Specialization, Qualification, ProviderService
from apps.orders.models import Order
from apps.payments.models import Wallet

User = get_user_model()

class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

class UserAdminForm(DashboardModelForm):
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','phone','role','is_active','is_staff','location_city','location_district']

class ProviderAdminForm(DashboardModelForm):
    class Meta:
        model = ProviderProfile
        fields = ['display_name','business_name','phone','email','bio','experience','experience_years','hourly_rate','address','location_city','location_district','latitude','longitude','status','verification_status','is_available','specializations','qualification_choices','admin_notes']
        widgets = {'bio': forms.Textarea(attrs={'rows': 3}), 'experience': forms.Textarea(attrs={'rows': 3}), 'admin_notes': forms.Textarea(attrs={'rows': 3})}

class ReasonActionForm(forms.Form):
    reason = forms.CharField(label='السبب / الملاحظة', required=True, widget=forms.Textarea(attrs={'class':'form-control','rows':3}))

class OptionalReasonActionForm(forms.Form):
    reason = forms.CharField(label='السبب / الملاحظة', required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':3}))

class VerificationDecisionForm(forms.ModelForm):
    class Meta:
        model = ProviderVerificationRequest
        fields = ['status', 'admin_note']
        widgets = {'admin_note': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}), 'status': forms.Select(attrs={'class': 'form-select'})}

class DocumentReviewForm(forms.Form):
    action = forms.ChoiceField(label='الإجراء', choices=[('approved','اعتماد'),('rejected','رفض'),('needs_additional_documents','طلب بديل')], widget=forms.Select(attrs={'class':'form-select'}))
    note = forms.CharField(label='ملاحظة الإدارة', required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':3}))

class CategoryForm(DashboardModelForm):
    class Meta: model = Category; fields = ['name','description','image','icon','parent','is_active','order']
class ServiceForm(DashboardModelForm):
    class Meta: model = Service; fields = ['provider','category','title','description','price_type','currency','price','delivery_time','image','status','is_featured']
class ProviderServiceForm(DashboardModelForm):
    class Meta: model = ProviderService; fields = ['provider','service','catalog_service','description','price','price_type','estimated_duration','is_active','approval_status']
class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(label='الحالة الجديدة', choices=Order.STATUS_CHOICES, widget=forms.Select(attrs={'class':'form-select'}))
    reason = forms.CharField(label='سبب التغيير', widget=forms.Textarea(attrs={'class':'form-control','rows':3}))
    force = forms.BooleanField(label='تغيير قسري بصلاحية المدير', required=False, widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
class NotificationForm(forms.Form):
    target = forms.ChoiceField(label='المستلمون', choices=[('all','كل المستخدمين'),('customers','العملاء'),('providers','مقدمو الخدمات'),('user','مستخدم محدد')], widget=forms.Select(attrs={'class':'form-select'}))
    user = forms.ModelChoiceField(label='مستخدم محدد', queryset=User.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-select'}))
    title = forms.CharField(label='العنوان', max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    message = forms.CharField(label='الرسالة', widget=forms.Textarea(attrs={'class':'form-control','rows':4}))
    def clean(self):
        data=super().clean()
        if data.get('target') == 'user' and not data.get('user'):
            raise forms.ValidationError('اختر المستخدم المحدد.')
        return data
class BulkActionForm(forms.Form):
    ids = forms.CharField(widget=forms.HiddenInput)
    action = forms.CharField(widget=forms.HiddenInput)
class CityForm(DashboardModelForm):
    class Meta: model = City; fields = ['name','is_active','order']
class DistrictForm(DashboardModelForm):
    class Meta: model = District; fields = ['city','name','is_active','order']
class ManagedServiceForm(DashboardModelForm):
    class Meta: model = ManagedService; fields = ['name','category','description','is_active','order']
class SpecializationForm(DashboardModelForm):
    class Meta: model = Specialization; fields = ['name','is_active','order']
class QualificationForm(DashboardModelForm):
    class Meta: model = Qualification; fields = ['name','is_active','order']
class WalletForm(DashboardModelForm):
    class Meta: model = Wallet; fields = ['name','code','color','is_active','display_order']
class TermsForm(DashboardModelForm):
    class Meta: model = TermsAndConditions; fields = ['version','content','commission_rate','is_active']
class GroupForm(DashboardModelForm):
    class Meta: model = Group; fields = ['name','permissions']
