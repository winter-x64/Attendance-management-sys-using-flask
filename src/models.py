from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    username = db.Column(db.String(50), unique=True)
    phone_number = db.Column(db.String(13), nullable=False)
    role = db.Column(db.String(20))
    notes = db.relationship('Attendance')
    subject = db.relationship('Subject')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    attendances = db.relationship('Attendance', backref='subject', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hour = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    present = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    