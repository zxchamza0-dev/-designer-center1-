# دليل النشر على Render.com

## خطوات النشر

### 1. إنشاء حساب على GitHub (إذا لم يكن لديك)
1. اذهب إلى https://github.com
2. سجل حساب جديد مجاناً

### 2. رفع المشروع على GitHub

#### الطريقة الأولى: من خلال الموقع
1. اذهب إلى https://github.com/new
2. أنشئ repository جديد باسم `designer-center`
3. اختر Public
4. لا تضف README (لأنه موجود بالفعل)
5. اضغط Create repository

#### الطريقة الثانية: من خلال Terminal
```bash
cd /Users/rajhidesgin/Downloads/CascadeProjects/designer_center

# تهيئة Git
git init
git add .
git commit -m "Initial commit - Designer Center"

# ربط بـ GitHub (استبدل YOUR_USERNAME باسم المستخدم)
git remote add origin https://github.com/YOUR_USERNAME/designer-center.git
git branch -M main
git push -u origin main
```

### 3. النشر على Render.com

1. **إنشاء حساب على Render**
   - اذهب إلى https://render.com
   - سجل دخول باستخدام حساب GitHub

2. **إنشاء Web Service جديد**
   - اضغط على "New +" في الأعلى
   - اختر "Web Service"
   - اختر repository الخاص بك `designer-center`
   - اضغط Connect

3. **إعدادات الخدمة**
   ```
   Name: designer-center
   Region: اختر الأقرب لك
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **إعدادات البيئة (Environment Variables)**
   أضف المتغيرات التالية:
   ```
   SECRET_KEY=your-super-secret-key-change-this
   FLASK_ENV=production
   ```

5. **اختر الخطة المجانية (Free)**

6. **اضغط "Create Web Service"**

### 4. انتظر النشر
- سيستغرق 5-10 دقائق
- ستحصل على رابط مثل: `https://designer-center.onrender.com`

### 5. الوصول للتطبيق
بعد اكتمال النشر، افتح الرابط الخاص بك:
```
https://your-app-name.onrender.com
```

## بيانات الدخول التجريبية

- **مسؤول**: admin@designer.com / 123456
- **عميل**: client@alnoor.com / 123456

## ملاحظات مهمة

### الخطة المجانية في Render
- ✅ مجانية تماماً
- ✅ SSL مجاني (HTTPS)
- ⚠️ التطبيق ينام بعد 15 دقيقة من عدم الاستخدام
- ⚠️ أول طلب بعد النوم قد يستغرق 30 ثانية

### تحديث التطبيق
عند تحديث الكود:
```bash
git add .
git commit -m "وصف التحديث"
git push
```
سيتم النشر تلقائياً على Render!

## بدائل أخرى

### Railway.app
1. اذهب إلى https://railway.app
2. سجل دخول بـ GitHub
3. اختر "New Project"
4. اختر "Deploy from GitHub repo"
5. اختر المشروع
6. سيتم النشر تلقائياً

### PythonAnywhere
1. اذهب إلى https://www.pythonanywhere.com
2. أنشئ حساب مجاني
3. افتح Bash console
4. استنسخ المشروع من GitHub
5. اتبع تعليمات النشر

## المساعدة

إذا واجهت أي مشاكل:
1. تحقق من Logs في Render Dashboard
2. تأكد من أن جميع الملفات موجودة
3. تأكد من صحة requirements.txt

---

**ملاحظة**: الخطة المجانية كافية للتجربة والمشاركة!
