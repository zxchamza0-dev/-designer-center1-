from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, date
import os
from flask_migrate import Migrate
import json
from sqlalchemy import func, extract, and_, or_
import calendar
from dateutil.relativedelta import relativedelta

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# إضافة متغيرات عامة للقوالب
@app.context_processor
def inject_globals():
    return {
        'date': date,
        'datetime': datetime
    }
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///designer_center.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# إنشاء مجلد الرفع إذا لم يكن موجوداً
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول أولاً'

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    user_type = db.Column(db.String(20), nullable=False, default='client')  # client, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    projects = db.relationship('Project', foreign_keys='Project.client_id', backref='client', lazy=True)
    admin_projects = db.relationship('Project', foreign_keys='Project.admin_id', backref='admin', lazy=True)
    invoices = db.relationship('Invoice', backref='client', lazy=True)
    expenses = db.relationship('Expense', backref='admin_user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='طلب جديد')  # طلب جديد, قيد التنفيذ, بانتظار المراجعة, مكتمل
    priority = db.Column(db.String(20), default='متوسط')  # منخفض, متوسط, عالي, عاجل
    budget = db.Column(db.Float)
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    progress = db.Column(db.Integer, default=0)  # 0-100
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    files = db.relationship('ProjectFile', backref='project', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    time_logs = db.relationship('TimeLog', backref='project', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='project', lazy=True)

class ProjectFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='معلق')  # معلق, قيد التنفيذ, مكتمل
    priority = db.Column(db.String(20), default='متوسط')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)

class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200))
    hours = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='مستحقة')  # مستحقة, مدفوعة, متأخرة
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)
    receipt_path = db.Column(db.String(500))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نماذج الفلاسك
class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني')

class RegisterForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('رقم الهاتف')
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('نوع المستخدم', choices=[('client', 'عميل'), ('admin', 'مسؤول')])

class ProjectForm(FlaskForm):
    title = StringField('عنوان المشروع', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('وصف المشروع')
    budget = DecimalField('الميزانية')
    due_date = DateField('تاريخ التسليم', format='%Y-%m-%d')
    priority = SelectField('الأولوية', choices=[
        ('منخفض', 'منخفض'),
        ('متوسط', 'متوسط'),
        ('عالي', 'عالي'),
        ('عاجل', 'عاجل')
    ])

class TaskForm(FlaskForm):
    title = StringField('عنوان المهمة', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('وصف المهمة')
    priority = SelectField('الأولوية', choices=[
        ('منخفض', 'منخفض'),
        ('متوسط', 'متوسط'),
        ('عالي', 'عالي'),
        ('عاجل', 'عاجل')
    ])
    due_date = DateField('تاريخ التسليم', format='%Y-%m-%d')

class TimeLogForm(FlaskForm):
    description = StringField('وصف العمل المنجز')
    hours = DecimalField('عدد الساعات', validators=[DataRequired()])
    date = DateField('التاريخ', format='%Y-%m-%d', default=date.today)

class ExpenseForm(FlaskForm):
    title = StringField('عنوان المصروفة', validators=[DataRequired(), Length(max=200)])
    amount = DecimalField('المبلغ', validators=[DataRequired()])
    category = StringField('الفئة')
    description = TextAreaField('الوصف')
    receipt = FileField('إيصال المصروفة', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'صور أو PDF فقط!')])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# إنشاء بيانات تجريبية
def create_demo_data():
    # إنشاء مسؤول تجريبي
    admin = User.query.filter_by(email='admin@designer.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@designer.com',
            full_name='مدير النظام',
            phone='0501234567',
            user_type='admin'
        )
        admin.set_password('123456')
        db.session.add(admin)

    # إنشاء عميل تجريبي
    client = User.query.filter_by(email='client@alnoor.com').first()
    if not client:
        client = User(
            username='client',
            email='client@alnoor.com',
            full_name='عميل تجريبي',
            phone='0507654321',
            user_type='client'
        )
        client.set_password('123456')
        db.session.add(client)

    db.session.commit()

    # إنشاء مشاريع تجريبية
    if Project.query.count() == 0:
        project1 = Project(
            title='تصميم شعار شركة النور',
            description='تصميم شعار احترافي لشركة النور للتقنية',
            status='طلب جديد',
            priority='عالي',
            budget=5000.0,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            client_id=client.id,
            admin_id=admin.id
        )
        project2 = Project(
            title='تطوير موقع إلكتروني',
            description='تطوير موقع إلكتروني تفاعلي باستخدام أحدث التقنيات',
            status='قيد التنفيذ',
            priority='متوسط',
            budget=15000.0,
            start_date=date.today() - timedelta(days=7),
            due_date=date.today() + timedelta(days=21),
            progress=35,
            client_id=client.id,
            admin_id=admin.id
        )
        project3 = Project(
            title='تصميم هوية بصرية',
            description='إنشاء هوية بصرية شاملة للعلامة التجارية',
            status='مكتمل',
            priority='متوسط',
            budget=8000.0,
            start_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=5),
            completed_date=date.today() - timedelta(days=5),
            progress=100,
            client_id=client.id,
            admin_id=admin.id
        )

        db.session.add_all([project1, project2, project3])
        db.session.commit()

        # إضافة مهام تجريبية
        task1 = Task(
            title='البحث والتحليل',
            description='دراسة السوق وتحليل المنافسين',
            status='مكتمل',
            priority='عالي',
            project_id=project2.id,
            assigned_to=admin.id,
            due_date=date.today() - timedelta(days=3),
            completed_at=date.today() - timedelta(days=2)
        )
        task2 = Task(
            title='تصميم الواجهات',
            description='تصميم واجهات المستخدم الأولية',
            status='قيد التنفيذ',
            priority='عالي',
            project_id=project2.id,
            assigned_to=admin.id,
            due_date=date.today() + timedelta(days=5)
        )

        db.session.add_all([task1, task2])
        db.session.commit()

# فلاتر جينجا المخصصة
@app.template_filter('strftime')
def strftime_filter(date, format='%Y-%m-%d'):
    if date:
        return date.strftime(format)
    return ''

@app.template_filter('number_format')
def number_format_filter(value):
    if value:
        return "{:,.2f}".format(float(value))
    return '0.00'

@app.template_filter('filesizeformat')
def filesizeformat_filter(value):
    """Format file size in bytes to human readable format"""
    if not value:
        return '0 B'
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"

# الصفحة الرئيسية
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    return render_template('index.html')

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        flash('بيانات تسجيل الدخول غير صحيحة أو الحساب معطل', 'error')

    return render_template('login.html', form=form)

# صفحة تسجيل الحساب الجديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('هذا البريد الإلكتروني مستخدم بالفعل', 'error')
        elif User.query.filter_by(username=form.username.data).first():
            flash('اسم المستخدم مستخدم بالفعل', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                user_type=form.user_type.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# لوحة تحكم العميل
@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.user_type != 'client':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    # إحصائيات المشاريع
    projects_stats = {
        'total': Project.query.filter_by(client_id=current_user.id).count(),
        'new': Project.query.filter_by(client_id=current_user.id, status='طلب جديد').count(),
        'in_progress': Project.query.filter_by(client_id=current_user.id, status='قيد التنفيذ').count(),
        'completed': Project.query.filter_by(client_id=current_user.id, status='مكتمل').count(),
        'review': Project.query.filter_by(client_id=current_user.id, status='بانتظار المراجعة').count()
    }

    # المشاريع الحديثة
    recent_projects = Project.query.filter_by(client_id=current_user.id).order_by(Project.created_at.desc()).limit(5).all()

    # المواعيد النهائية القادمة
    upcoming_deadlines = Project.query.filter(
        and_(
            Project.client_id == current_user.id,
            Project.due_date >= date.today(),
            Project.status != 'مكتمل'
        )
    ).order_by(Project.due_date).limit(5).all()

    # الفواتير
    invoices = Invoice.query.filter_by(client_id=current_user.id).order_by(Invoice.created_at.desc()).limit(5).all()

    # الإشعارات
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).limit(5).all()

    return render_template('client_dashboard.html',
                         projects_stats=projects_stats,
                         recent_projects=recent_projects,
                         upcoming_deadlines=upcoming_deadlines,
                         invoices=invoices,
                         notifications=notifications)

# لوحة تحكم المسؤول
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    # إحصائيات عامة
    stats = {
        'total_projects': Project.query.count(),
        'new_projects': Project.query.filter_by(status='طلب جديد').count(),
        'in_progress': Project.query.filter_by(status='قيد التنفيذ').count(),
        'completed': Project.query.filter_by(status='مكتمل').count(),
        'review': Project.query.filter_by(status='بانتظار المراجعة').count(),
        'total_clients': User.query.filter_by(user_type='client').count(),
        'total_revenue': db.session.query(func.sum(Invoice.amount)).filter(Invoice.status == 'مدفوعة').scalar() or 0,
        'pending_invoices': Invoice.query.filter_by(status='مستحقة').count()
    }

    # مشاريع قيد التنفيذ
    in_progress_projects = Project.query.filter_by(status='قيد التنفيذ').order_by(Project.due_date).limit(10).all()

    # طلبات جديدة
    new_projects = Project.query.filter_by(status='طلب جديد').order_by(Project.created_at.desc()).limit(10).all()

    # المواعيد النهائية القريبة
    upcoming_deadlines = Project.query.filter(
        and_(
            Project.due_date >= date.today(),
            Project.due_date <= date.today() + timedelta(days=7),
            Project.status != 'مكتمل'
        )
    ).order_by(Project.due_date).limit(5).all()

    # إحصائيات شهرية
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_stats = {
        'projects_completed': Project.query.filter(
            extract('month', Project.completed_date) == current_month,
            extract('year', Project.completed_date) == current_year
        ).count(),
        'revenue': db.session.query(func.sum(Invoice.amount)).filter(
            and_(
                extract('month', Invoice.paid_date) == current_month,
                extract('year', Invoice.paid_date) == current_year,
                Invoice.status == 'مدفوعة'
            )
        ).scalar() or 0,
        'new_clients': User.query.filter(
            extract('month', User.created_at) == current_month,
            extract('year', User.created_at) == current_year,
            User.user_type == 'client'
        ).count()
    }

    return render_template('admin_dashboard.html',
                         stats=stats,
                         in_progress_projects=in_progress_projects,
                         new_projects=new_projects,
                         upcoming_deadlines=upcoming_deadlines,
                         monthly_stats=monthly_stats)

# صفحة مشاريع العميل
@app.route('/client/projects')
@login_required
def client_projects():
    if current_user.user_type != 'client':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    projects = Project.query.filter_by(client_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('client_projects.html', projects=projects)

# صفحة طلب مشروع جديد
@app.route('/client/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if current_user.user_type != 'client':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            budget=form.budget.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            client_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()

        # إضافة إشعار للمسؤول
        admin = User.query.filter_by(user_type='admin').first()
        if admin:
            notification = Notification(
                user_id=admin.id,
                title='طلب مشروع جديد',
                message=f'طلب مشروع جديد من {current_user.full_name}: {project.title}',
                type='info'
            )
            db.session.add(notification)
            db.session.commit()

        flash('تم تقديم طلب المشروع بنجاح! سيتم مراجعته قريباً', 'success')
        return redirect(url_for('client_projects'))

    return render_template('new_project.html', form=form)

# صفحة عرض مشروع
@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)

    # التحقق من الصلاحية
    if current_user.user_type == 'client' and project.client_id != current_user.id:
        flash('ليس لديك صلاحية عرض هذا المشروع', 'error')
        return redirect(url_for('index'))

    files = ProjectFile.query.filter_by(project_id=project_id).all()
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
    time_logs = TimeLog.query.filter_by(project_id=project_id).order_by(TimeLog.created_at.desc()).all()

    return render_template('view_project.html',
                         project=project,
                         files=files,
                         tasks=tasks,
                         time_logs=time_logs)

# صفحة رفع ملفات
@app.route('/project/<int:project_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)

    # التحقق من الصلاحية
    if current_user.user_type == 'client' and project.client_id != current_user.id:
        flash('ليس لديك صلاحية رفع الملفات لهذا المشروع', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار أي ملف', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار أي ملف', 'error')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            project_file = ProjectFile(
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type,
                project_id=project_id,
                uploaded_by=current_user.id
            )
            db.session.add(project_file)
            db.session.commit()

            flash('تم رفع الملف بنجاح', 'success')
            return redirect(url_for('view_project', project_id=project_id))

    return render_template('upload_file.html', project=project)

# صفحة تحميل ملف
@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    project_file = ProjectFile.query.get_or_404(file_id)
    project = Project.query.get_or_404(project_file.project_id)

    # التحقق من الصلاحية
    if current_user.user_type == 'client' and project.client_id != current_user.id:
        flash('ليس لديك صلاحية تحميل هذا الملف', 'error')
        return redirect(url_for('index'))

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        project_file.filename,
        as_attachment=True,
        download_name=project_file.original_filename
    )

# لوحة إدارة المشاريع (Kanban)
@app.route('/admin/projects')
@login_required
def admin_projects():
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    projects = {
        'new': Project.query.filter_by(status='طلب جديد').order_by(Project.created_at.desc()).all(),
        'in_progress': Project.query.filter_by(status='قيد التنفيذ').order_by(Project.due_date).all(),
        'review': Project.query.filter_by(status='بانتظار المراجعة').order_by(Project.due_date).all(),
        'completed': Project.query.filter_by(status='مكتمل').order_by(Project.completed_date.desc()).all()
    }

    return render_template('admin_projects.html', projects=projects)

# تحديث حالة المشروع
@app.route('/admin/project/<int:project_id>/status', methods=['POST'])
@login_required
def update_project_status(project_id):
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})

    project = Project.query.get_or_404(project_id)
    new_status = request.json.get('status')

    if new_status not in ['طلب جديد', 'قيد التنفيذ', 'بانتظار المراجعة', 'مكتمل']:
        return jsonify({'success': False, 'message': 'حالة غير صالحة'})

    project.status = new_status
    if new_status == 'مكتمل':
        project.completed_date = date.today()
        project.progress = 100
    elif new_status == 'قيد التنفيذ':
        project.progress = 50

    db.session.commit()

    # إضافة إشعار للعميل
    notification = Notification(
        user_id=project.client_id,
        title='تحديث حالة المشروع',
        message=f'تم تحديث حالة مشروع "{project.title}" إلى: {new_status}',
        type='info'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': 'تم تحديث الحالة بنجاح'})

# إضافة مهمة للمشروع
@app.route('/project/<int:project_id>/task/add', methods=['GET', 'POST'])
@login_required
def add_task(project_id):
    project = Project.query.get_or_404(project_id)

    # التحقق من الصلاحية
    if current_user.user_type == 'client' and project.client_id != current_user.id:
        flash('ليس لديك صلاحية إضافة مهام لهذا المشروع', 'error')
        return redirect(url_for('index'))

    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            project_id=project_id,
            assigned_to=current_user.id if current_user.user_type == 'admin' else project.admin_id
        )
        db.session.add(task)
        db.session.commit()

        flash('تم إضافة المهمة بنجاح', 'success')
        return redirect(url_for('view_project', project_id=project_id))

    return render_template('add_task.html', form=form, project=project)

# إضافة سجل وقت عمل
@app.route('/project/<int:project_id>/timelog/add', methods=['GET', 'POST'])
@login_required
def add_timelog(project_id):
    project = Project.query.get_or_404(project_id)

    # فقط المسؤول يمكنه إضافة سجلات الوقت
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية إضافة سجلات الوقت', 'error')
        return redirect(url_for('index'))

    form = TimeLogForm()
    if form.validate_on_submit():
        timelog = TimeLog(
            project_id=project_id,
            user_id=current_user.id,
            description=form.description.data,
            hours=form.hours.data,
            date=form.date.data
        )
        db.session.add(timelog)
        db.session.commit()

        flash('تم إضافة سجل الوقت بنجاح', 'success')
        return redirect(url_for('view_project', project_id=project_id))

    return render_template('add_timelog.html', form=form, project=project)

# قائمة العملاء
@app.route('/admin/clients')
@login_required
def admin_clients():
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    clients = User.query.filter_by(user_type='client').all()
    return render_template('admin_clients.html', clients=clients)

# عرض ملف عميل
@app.route('/admin/client/<int:client_id>')
@login_required
def view_client(client_id):
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    client = User.query.get_or_404(client_id)
    if client.user_type != 'client':
        flash('المستخدم المحدد ليس عميل', 'error')
        return redirect(url_for('admin_clients'))

    # مشاريع العميل
    projects = Project.query.filter_by(client_id=client_id).order_by(Project.created_at.desc()).all()

    # فواتير العميل
    invoices = Invoice.query.filter_by(client_id=client_id).order_by(Invoice.created_at.desc()).all()

    # إحصائيات العميل
    client_stats = {
        'total_projects': len(projects),
        'completed_projects': len([p for p in projects if p.status == 'مكتمل']),
        'total_paid': sum([inv.amount for inv in invoices if inv.status == 'مدفوعة']),
        'pending_amount': sum([inv.amount for inv in invoices if inv.status == 'مستحقة'])
    }

    return render_template('view_client.html',
                         client=client,
                         projects=projects,
                         invoices=invoices,
                         client_stats=client_stats)

# المصروفات
@app.route('/admin/expenses', methods=['GET', 'POST'])
@login_required
def admin_expenses():
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        form = ExpenseForm()
        if form.validate_on_submit():
            expense = Expense(
                title=form.title.data,
                amount=form.amount.data,
                category=form.category.data,
                description=form.description.data,
                admin_id=current_user.id
            )

            if form.receipt.data:
                filename = secure_filename(form.receipt.data.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                form.receipt.data.save(file_path)
                expense.receipt_path = file_path

            db.session.add(expense)
            db.session.commit()

            flash('تم إضافة المصروفة بنجاح', 'success')
            return redirect(url_for('admin_expenses'))
    else:
        form = ExpenseForm()

    expenses = Expense.query.filter_by(admin_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('admin_expenses.html', form=form, expenses=expenses)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_demo_data()
    
    # للتشغيل المحلي
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', host='0.0.0.0', port=port)
