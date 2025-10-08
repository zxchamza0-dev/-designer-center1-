# 🚀 نشر التطبيق بسرعة

## الطريقة الأسرع (5 دقائق)

### 1️⃣ رفع على GitHub

```bash
cd /Users/rajhidesgin/Downloads/CascadeProjects/designer_center

# تهيئة Git
git init
git add .
git commit -m "Designer Center App"

# إنشاء repository على GitHub أولاً من https://github.com/new
# ثم نفذ (استبدل YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/designer-center.git
git branch -M main
git push -u origin main
```

### 2️⃣ النشر على Render.com

1. اذهب إلى https://render.com
2. سجل دخول بـ GitHub
3. اضغط "New +" → "Web Service"
4. اختر repository: `designer-center`
5. الإعدادات:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. أضف متغير بيئة:
   - `SECRET_KEY` = `your-secret-key-123`
7. اختر Free Plan
8. اضغط "Create Web Service"

### 3️⃣ انتهى! 🎉

ستحصل على رابط مثل:
```
https://designer-center-xxxx.onrender.com
```

## بيانات الدخول

- **مسؤول**: admin@designer.com / 123456
- **عميل**: client@alnoor.com / 123456

---

## بدائل سريعة أخرى

### Railway.app (أسهل)
1. https://railway.app
2. "New Project" → "Deploy from GitHub"
3. اختر المشروع → تم!

### Vercel (للمشاريع الصغيرة)
```bash
npm i -g vercel
vercel
```

---

**ملاحظة**: الخطط المجانية كافية للتجربة والمشاركة مع الأصدقاء!
