from django.db import migrations

DOCUMENT_TYPES = [
    ('IDENTITY', 'الهوية', True),
    ('CV', 'CV / السيرة الذاتية', True),
    ('EXPERIENCE_CERTIFICATE', 'شهادة خبرة', False),
    ('PROFESSIONAL_CERTIFICATE', 'شهادة مهنية', False),
    ('ACADEMIC_CERTIFICATE', 'شهادة أكاديمية', False),
    ('COMMERCIAL_REGISTRATION', 'سجل تجاري', False),
    ('OTHER', 'مستندات أخرى', False),
]

def seed_document_types(apps, schema_editor):
    ProviderDocumentType = apps.get_model('accounts', 'ProviderDocumentType')
    for code, name, required in DOCUMENT_TYPES:
        ProviderDocumentType.objects.update_or_create(code=code, defaults={'name': name, 'is_required': required, 'is_active': True})

class Migration(migrations.Migration):
    dependencies = [('accounts', '0008_alter_providerdocument_file')]
    operations = [migrations.RunPython(seed_document_types, migrations.RunPython.noop)]
