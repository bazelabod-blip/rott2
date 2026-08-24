from django import forms
from apps.accounts.models import ProviderVerificationRequest
from apps.core.models import City, District, TermsAndConditions
from apps.marketplace.models import ManagedService, Specialization, Qualification
from apps.payments.models import Wallet

class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)

class VerificationDecisionForm(forms.ModelForm):
    class Meta:
        model = ProviderVerificationRequest
        fields = ['status', 'admin_note']
        widgets = {'admin_note': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}), 'status': forms.Select(attrs={'class': 'form-select'})}

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
