# نشر البوت على Render

## خطوات النشر:

### 1. إنشاء حساب على Render
- قم بإنشاء حساب مجاني على [render.com](https://render.com)

### 2. إنشاء Web Service جديد
1. اضغط على "New +" واختر "Web Service"
2. اربط حساب GitHub الخاص بك أو ارفع الملفات يدوياً

### 3. إعدادات الخدمة
- **Name**: pixabay-telegram-bot
- **Runtime**: Python 3
- **Build Command**: `pip install -r render_requirements.txt`
- **Start Command**: `python main.py`

### 4. متغيرات البيئة المطلوبة
أضف هذه المتغيرات في قسم "Environment Variables":
```
BOT_TOKEN=8496475334:AAFVBYMsb_d_K80YkD06V3ZlcASS2jzV0uQ 
ADMIN_ID=7251748706
PIXABAY_API_KEY=51444506-bffefcaf12816bd85a20222d1
RENDER=true
```

### 5. الملفات المطلوبة للنشر
- `main.py` - الكود الرئيسي للبوت
- `render_requirements.txt` - المكتبات المطلوبة
- `Procfile` - تعليمات تشغيل الخدمة

### 6. بعد النشر
- سيحصل البوت على رابط مثل: `https://your-service-name.onrender.com`
- البوت سيعمل بنظام webhook بدلاً من polling للأداء الأفضل

## ملاحظات مهمة:
- الخدمة المجانية على Render تتوقف بعد 15 دقيقة من عدم النشاط
- لحل هذه المشكلة، يمكن استخدام خدمة Uptime Robot للإبقاء على البوت نشطاً
- البوت يدعم كلاً من webhook (للإنتاج) و polling (للتطوير)