# منصة سوق الخدمات (Service Marketplace)

منصة ويب متكاملة لربط مقدمي الخدمات مع العملاء في مختلف المجالات، مبنية باستخدام Django وBootstrap 5.

## 📋 المميزات الرئيسية

- ✅ نظام تسجيل ودخول متكامل مع أدوار متعددة (عميل، مقدم خدمة، مدير)
- ✅ تصفح الخدمات والبحث والفلترة
- ✅ نظام طلبات متقدم مع تتبع الحالة
- ✅ محادثة مباشرة بين العملاء ومقدمي الخدمات
- ✅ نظام تقييمات شامل
- ✅ لوحة تحكم إدارية متكاملة
- ✅ دعم كامل للغة العربية (RTL)
- ✅ تصميم متجاوب لجميع الأجهزة

## 🛠 التقنيات المستخدمة

- **Backend**: Django 4.2+
- **Frontend**: Bootstrap 5 (RTL), HTML5, CSS3, JavaScript
- **Database**: SQLite (التطوير) / PostgreSQL (الإنتاج)
- **Additional**: Django Crispy Forms, WhiteNoise, Pillow

## 📦 التثبيت والإعداد

### 1. المتطلبات الأساسية

- Python 3.10 أو أحدث
- pip (مدير حزم Python)

### 2. تنزيل المشروع

```bash
git clone <repository-url>
cd service_marketplace
```

### 3. إنشاء البيئة الافتراضية

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

إذا واجهت مشاكل في الاتصال بـ PyPI، جرب:
```bash
pip install --default-timeout=100 Django psycopg2-binary python-decouple Pillow django-crispy-forms crispy-bootstrap5 gunicorn whitenoise
```

### 5. إعداد المتغيرات البيئية

انسخ ملف `.env.example` إلى `.env`:

**Windows:**
```powershell
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

ثم قم بتعديل ملف `.env` وضع قيمة آمنة لـ `SECRET_KEY`:

```env
SECRET_KEY=your-very-secret-and-random-key-here
DEBUG=True
```

### 6. إنشاء قاعدة البيانات

```bash
python manage.py migrate
```

### 7. إنشاء حساب مدير

```bash
python manage.py createsuperuser
```

أدخل:
- اسم المستخدم
- البريد الإلكتروني
- كلمة المرور

### 8. تشغيل السيرفر

```bash
python manage.py runserver
```

افتح المتصفح على: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 🚀 الاستخدام

### الوصول للصفحة الرئيسية
```
http://127.0.0.1:8000/
```

### الوصول للوحة الإدارة
```
http://127.0.0.1:8000/admin/
```
(استخدم حساب المدير الذي أنشأته)

## 📁 هيكل المشروع

```
service_marketplace/
├── config/                 # إعدادات المشروع الرئيسية
│   ├── settings.py        # الإعدادات
│   ├── urls.py            # URLs الرئيسية
│   ├── wsgi.py            # WSGI للإنتاج
│   └── asgi.py            # ASGI للدعم Async
├── apps/                   # تطبيقات المشروع
│   ├── accounts/          # (قريباً) إدارة المستخدمين
│   ├── marketplace/       # (قريباً) الخدمات والتصنيفات
│   ├── orders/            # (قريباً) الطلبات
│   ├── chat/              # (قريباً) المحادثات
│   ├── reviews/           # (قريباً) التقييمات
│   └── dashboard/         # (قريباً) لوحة الإدارة
├── templates/              # القوالب HTML
│   ├── base.html          # القالب الأساسي
│   ├── home.html          # الصفحة الرئيسية
│   └── partials/          # أجزاء القوالب
├── static/                 # الملفات الثابتة
│   ├── css/               # ملفات CSS
│   ├── js/                # ملفات JavaScript
│   └── img/               # الصور
├── media/                  # ملفات المستخدمين المرفوعة
├── manage.py               # أداة إدارة Django
├── requirements.txt        # المتطلبات
├── .env.example           # مثال المتغيرات البيئية
└── README.md              # هذا الملف
```

## 🧪 الاختبارات

لتشغيل الاختبارات (سيتم إضافتها في المراحل القادمة):

```bash
python manage.py test
```

## 🔐 الأمان

- ✅ حماية CSRF مفعلة
- ✅ مفتاح سري عشوائي (تأكد من تغييره في الإنتاج)
- ✅ التحقق من الصلاحيات في جميع الـ Views
- ✅ Validation قوي للنماذج

## 📝 المراحل القادمة

- [x] **المرحلة 1**: تهيئة المشروع والتشغيل ✅
- [ ] **المرحلة 2**: نظام المستخدمين والأدوار
- [ ] **المرحلة 3**: التصنيفات والخدمات
- [ ] **المرحلة 4**: الطلبات وإدارة الحالات
- [ ] **المرحلة 5**: نظام المحادثة
- [ ] **المرحلة 6**: التقييمات
- [ ] **المرحلة 7**: لوحة الإدارة
- [ ] **المرحلة 8**: الأمان والاختبارات
- [ ] **المرحلة 9**: الإعداد للإنتاج

## 🤝 المساهمة

هذا المشروع تعليمي. يمكنك المساهمة بـ:
- الإبلاغ عن الأخطاء
- اقتراح مميزات جديدة
- تحسين الكود

## 📄 الترخيص

MIT License

## 📞 الدعم

للأسئلة أو الدعم، تواصل معنا على: support@servicemarketplace.com

---

**تم بناءه بـ ❤️ باستخدام Django**
venv/Scripts/Activate.ps1
python manage.py runserver

## Marketplace Platform Update

### Structure
- `apps.accounts`: custom users, provider profiles, provider verification documents, registration/profile views.
- `apps.marketplace`: categories, catalog services, provider service offerings, search and provider/service browsing.
- `apps.orders`: order lifecycle, messages, delivery, cancellation/dispute-ready states.
- `apps.payments`: payment records, commission snapshots, and gateway abstraction.
- `apps.core`: terms versioning, terms acceptance, notifications, audit log, platform settings, shared commission calculation.

### Environment variables
Use `.env` (not committed) for `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` if switching from SQLite, `PAYMENT_GATEWAY_KEY`, `MAPS_API_KEY`, and email credentials. Jazzmin is loaded only when installed so local checks are not blocked by missing optional admin theme packages.

### Database and migrations
Run:
```bash
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

### Admin
Django Admin manages users, provider profiles, verification documents, document types, categories, services, provider services, orders, payments, commissions, terms, notifications, audit logs, and platform settings.

### Payments
Payment infrastructure is implemented with a `Payment` model, `CommissionRecord`, `calculate_commission()`, and a `ManualPaymentGateway` adapter for internal/manual flows and tests. **NEEDS EXTERNAL CONFIGURATION** for a production payment gateway.

### Maps
Provider profiles store city, district, latitude, longitude, and service radius. Map provider integration is intentionally abstract and **NEEDS EXTERNAL CONFIGURATION** for geocoding/map rendering credentials.

### Documentation
See `docs/ERD.md` for the implemented data model. Flow documentation was intentionally kept out of the repository to avoid extra generated artifacts.

### Remaining Marketplace Completion
- Map/location: provider profile editing uses Leaflet + OpenStreetMap tiles in development. Clicking or dragging the marker writes latitude/longitude into hidden form fields, then Django validates and saves them on `ProviderProfile`. Public provider profile pages render the saved marker without exposing documents.
- Provider activation: providers must have `status=active` and `verification_status=verified` before creating `Service` or `ProviderService` records; the backend enforces this in views and model validation.
- Provider documents: seeded document types include Identity, CV, experience/professional/academic certificates, commercial registration, and other. Uploaded documents use private storage and a protected download view.
- Payments: customers create payment records from payment-pending orders. DEBUG-only test actions can mark success/failure; production electronic gateway integration still needs external credentials.
- Search: navbar/global search and provider search use Django ORM over public providers, services, and categories, with provider filters for category, service, city, district, rating, experience, availability, and optional coordinate radius.
