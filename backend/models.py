import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patients = db.relationship("Patient", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    diabetes_duration = db.Column(db.Float, nullable=True)
    hba1c = db.Column(db.Float, nullable=True)
    fasting_blood_sugar = db.Column(db.Float, nullable=True)
    random_blood_sugar = db.Column(db.Float, nullable=True)
    current_medication = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    symptoms = db.relationship("Symptom", backref="patient", uselist=False, cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", backref="patient", lazy=True, cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="patient", lazy=True, cascade="all, delete-orphan")
    images = db.relationship("Image", backref="patient", lazy=True, cascade="all, delete-orphan")


class Symptom(db.Model):
    __tablename__ = "symptoms"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    redness = db.Column(db.Boolean, default=False)
    swelling = db.Column(db.Boolean, default=False)
    pain = db.Column(db.Boolean, default=False)
    fever = db.Column(db.Boolean, default=False)
    numbness = db.Column(db.Boolean, default=False)
    cracks = db.Column(db.Boolean, default=False)
    previous_foot_ulcer = db.Column(db.Boolean, default=False)
    previous_cellulitis = db.Column(db.Boolean, default=False)


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    prediction = db.Column(db.String(80), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(40), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    left_image = db.Column(db.String(255), nullable=True)
    right_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
