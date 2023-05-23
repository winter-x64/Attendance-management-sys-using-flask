from flask import Flask, request, redirect, current_app, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, timedelta

from twilio.rest import Client
import keys

db = SQLAlchemy()
DB_NAME = "database.db"

#? -------------------------- Functions --------------------------------
def get_attendance_percentage(student_id, subject_id):
    total_attendance = Attendance.query.filter_by(user_id=student_id, subject_id=subject_id).count()
    present_attendance = Attendance.query.filter_by(user_id=student_id, subject_id=subject_id, present=True).count()
    if total_attendance == 0:
        return 0
    else:
        return round(present_attendance / total_attendance * 100, 2)

def MainApp():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    # DB
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Attendance , Subject
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Function to send SMS using Twilio
    def send_sms(to_number, body):
        client = Client(keys.account_sid,keys.auth_token)
        message = client.messages.create(
            body=body,
            from_=keys.twilio_number,
            to=to_number
        )

        return message.sid

    # Route to send attendance reports via SMS
    @app.route('/send_attendance_sms')
    @login_required
    def send_attendance_sms():
        if not current_user.role == 'teacher':
            return 'Access denied', 403

        students = User.query.filter_by(role='student').all()
        subjects = Subject.query.all()

        for student in students:
            
            attendance_report = f"Attendance Report for {student.username}:\n"
            for subject in subjects:
                attendance_percentage = get_attendance_percentage(student_id = student.id, subject_id = subject.id)
                attendance_report += f"{subject.name}: {attendance_percentage}%\n"

            # Send the attendance report via SMS
            send_sms(student.phone_number, attendance_report)

        flash('Attendance reports sent successfully!', category='success')
        return redirect(url_for('views.teacher_home'))
        
    # Return the app to the main file
    return app
            


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
        