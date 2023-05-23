
#? -------------------------- Import --------------------------------
#* 3rd Party modules
from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from twilio.rest import Client
import keys

#* custom modules
from . import db
from .models import User, Subject, Attendance

#? -------------------------- Blueprint --------------------------------
views = Blueprint('views', __name__)

#? -------------------------- Functions --------------------------------
def get_attendance_percentage(student_id, subject_id):
    total_attendance = Attendance.query.filter_by(user_id=student_id, subject_id=subject_id).count()
    present_attendance = Attendance.query.filter_by(user_id=student_id, subject_id=subject_id, present=True).count()
    if total_attendance == 0:
        return 0
    else:
        return round(present_attendance / total_attendance * 100, 2)

#* --------------------------------- Home --------------------------------
#? -------------------------- Home - Landing Page --------------------------------
@views.route('/')
def index():
    return render_template("index.html", user = current_user)

#* -------------------------- Student --------------------------------
#? ----------------------- Student Home --------------------------------
@views.route('/student_home', methods=['GET', 'POST'])
@login_required
def student_home():
    if not current_user.role == 'student':
        return 'Access denied', 403
    
    subjects = Subject.query.all()
    
    attendance_data = []
    for subject in subjects:
        attendance_count = Attendance.query.filter_by(user_id=current_user.id, subject_id=subject.id).count()
        total_lectures = len(subject.attendances)
        attendance_percentage = (attendance_count / total_lectures) * 100 if total_lectures > 0 else 0
        
        attendance_data.append({
            'subject': subject.name,
            'attendance_percentage': round(attendance_percentage, 2)
        })
    subj = Subject.query.all() 
    return render_template('student/student_home.html', name=current_user.username, attendance=attendance_data, user = current_user)

#* -------------------------- Teacher --------------------------------
#? ----------------------- Teacher Home --------------------------------
@views.route('/teacher_home', methods=['GET', 'POST'])
@login_required
def teacher_home():

    if not current_user.role == 'teacher':
        return 'Access denied', 403

    students = User.query.filter_by(role='student').all()
    subjects = Subject.query.all()

    attendance_data = []    
    for student in students:
        student_attendance = []
        for subject in subjects:
            attendance_percentage = get_attendance_percentage(student_id = student.id, subject_id = subject.id)
            student_attendance.append({
                'subject': subject.name,
                'attendance_percentage': attendance_percentage
            })

        attendance_data.append({
            'student_name': student.username,
            'attendance': student_attendance
        })

    subjectList = []
    for subject in subjects:
        subjectList.append({'subject': subject.name})

    return render_template('teacher/teacher_home.html', attendance_data=attendance_data, user=current_user, subjectList = subjectList)

#? -------------------------- Subject - ADD --------------------------------
@views.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    if request.method == 'POST':
        # Add new subject to database
        name = request.form['name']
        subject = Subject(name=name, user_id = current_user.id)
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for('views.add_subject'))
    else:
        # Display form for adding new subject
        SubjList = Subject.query.all()
        return render_template('teacher/add_subject.html', user=current_user, Subjects = SubjList)


#? -------------------------- Search --------------------------------
@views.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        subject_id = request.form['subject']
        
        # Get The percentage
        percentage = get_attendance_percentage(current_user.id, subject_id)
        SubjList = Subject.query.all()
        subject = Subject.query.filter_by(id=subject_id).first()
        return render_template("student/att.html", percentage = percentage, user = current_user, subject = subject, subj = SubjList)
    else:
        return redirect(url_for('views.student_home'))

#? -------------------------- Teacher - Attendance - ADD --------------------------------
@views.route('/add_attendence', methods=['GET', 'POST'])
@login_required
def add_attendence():
    if request.method == 'POST': 
        date = request.form.get('date')
        subject_id = request.form.get('subject')
        hour = request.form.get('hour')

        # Loop through all students and add attendance records for checked checkboxes
        for student in User.query.filter_by(role='student').all():
            present = True if request.form.get('present-{}'.format(student.id)) else False

            attendance = Attendance(date=date, present=present, user_id=student.id, subject_id=subject_id, hour=hour)
            db.session.add(attendance)
            db.session.commit()

        return redirect(url_for('views.add_attendence'))

    users = User.query.all()
    SubjList = Subject.query.all()
    return render_template("teacher/add_attendance.html", user=current_user, users=users, SubjList=SubjList)

#? -------------------------- Teacher - User - List - ALL --------------------------------
@views.route('/list_user', methods=['GET', 'POST'])
def list_user():
    users = User.query.all()
    return render_template("teacher/teacher_list_user.html", user=current_user, users=users)

#? -------------------------- Teacher - User - Delete - ALL --------------------------------
@views.route('/delete_user/<int:user_id>', methods=['POST', 'DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.role == 'teacher':
        return 'Access denied', 403

    # Delete associated attendance records
    attendance_records = Attendance.query.filter_by(user_id=user_id).all()
    for attendance in attendance_records:
        db.session.delete(attendance)
    
    # Delete the user
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    
    db.session.commit()
    flash('User {} has been deleted'.format(user.username))
    return redirect(url_for('views.list_user'))


#? -------------------------- Teacher - Attendance - Update --------------------------------
@views.route('/update_attendence', methods=['GET', 'POST'])
@login_required
def update_attendence():
    if request.method == 'POST':
        date = request.form.get('date')
        subject_id = request.form.get('subject')
        hour = request.form.get('hour')

        # Loop through all students and process attendance records
        for student in User.query.filter_by(role='student').all():
            present = True if request.form.get('present-{}'.format(student.id)) else False

            # Check if attendance record already exists for the student and subject
            attendance = Attendance.query.filter_by(date=date, subject_id=subject_id, user_id=student.id).first()

            if attendance:
                # Attendance record exists, update it
                attendance.present = present
                attendance.hour = hour
            else:
                # Attendance record doesn't exist, create a new one
                attendance = Attendance(date=date, present=present, user_id=student.id, subject_id=subject_id, hour=hour)
                db.session.add(attendance)

        db.session.commit()

        return redirect(url_for('views.add_attendence'))

    users = User.query.all()
    SubjList = Subject.query.all()
    return render_template("teacher/teacher_update.html", user=current_user, users=users, SubjList=SubjList)
