from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField
from flask_wtf.csrf import CSRFProtect
from wtforms.validators import DataRequired, NumberRange
from functools import wraps

app = Flask(__name__)

# Setup Secret Key for CSRF
app.config['SECRET_KEY'] = 'secretkey12345'
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model untuk student
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

# Flask-WTF Form untuk student
class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1)])
    grade = StringField('Grade', validators=[DataRequired()])

# Flask-WTF Form untuk login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# Middleware untuk memeriksa autentikasi
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Harus login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if username == 'admin' and password == 'kelompok9':
            session['user_id'] = username
            flash('Login berhasil.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
    
    return render_template('login.html', form=form)

# Route logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout berhasil.', 'success')
    return redirect(url_for('index'))

# Route untuk halaman tabel student (tidak memerlukan login untuk melihat)
@app.route('/')
def index():
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

# Route untuk menambah student
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        name = form.name.data
        age = form.age.data
        grade = form.grade.data
        
        query = text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)")
        db.session.execute(query, {'name': name, 'age': age, 'grade': grade})
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_student.html', form=form)

# Route untuk menghapus student
@app.route('/delete/<string:id>')
@login_required
def delete_student(id):
    db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    return redirect(url_for('index'))

# Route untuk mengedit student
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    form = StudentForm()
    if request.method == 'POST' and form.validate_on_submit():
        name = form.name.data
        age = form.age.data
        grade = form.grade.data
        
        query = text("UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id")
        db.session.execute(query, {'name': name, 'age': age, 'grade': grade, 'id': id})
        db.session.commit()
        return redirect(url_for('index'))
    else:
        student = db.session.execute(text("SELECT * FROM student WHERE id=:id"), {'id': id}).fetchone()
        if not student:
            return "Student tidak ditemukan", 404
        
        # Isi form dengan data awal
        form.name.data = student.name
        form.age.data = student.age
        form.grade.data = student.grade
        return render_template('edit.html', form=form, student=student)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)