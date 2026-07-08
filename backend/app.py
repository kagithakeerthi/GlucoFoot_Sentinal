import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

try:
    from .models import db, User, Patient, Symptom, Prediction, Report, Image
    from .prediction import predict_condition
except ImportError:
    from models import db, User, Patient, Symptom, Prediction, Report, Image
    from prediction import predict_condition

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "glucofoot.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")

os.makedirs(DATABASE_DIR, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "glucofoot-sentinel-dev"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORT_FOLDER"] = REPORT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# Allow localhost dev origins (accept any localhost port) to avoid CORS issues when Vite auto-changes ports
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": r"^http://localhost(:[0-9]+)?$"}})
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def ensure_db():
    if not app.config.get("_db_ready", False):
        with app.app_context():
            db.create_all()
            ensure_seed_user()
            app.config["_db_ready"] = True


def ensure_seed_user():
    admin = User.query.filter_by(email="admin@glucofoot.com").first()
    if not admin:
        admin = User(username="admin", email="admin@glucofoot.com", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Username, email, and password are required"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400
    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"message": "Registration successful", "user": serialize_user(user)})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=data.get("email", "")).first()
    if user and user.check_password(data.get("password", "")):
        login_user(user)
        return jsonify({"message": "Login successful", "user": serialize_user(user)})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"})


@app.route("/api/auth/me")
@login_required
def me():
    return jsonify({"user": serialize_user(current_user)})


@app.route("/api/patients", methods=["GET", "POST"])
@login_required
def patients():
    if request.method == "GET":
        patients_list = Patient.query.filter_by(user_id=current_user.id).order_by(Patient.created_at.desc()).all()
        return jsonify({"patients": [serialize_patient(p) for p in patients_list]})

    form = request.form
    patient_data = {
        "name": form.get("name"),
        "age": int(form.get("age", 0) or 0),
        "gender": form.get("gender", "Not specified"),
        "weight": float(form.get("weight", 0) or 0),
        "height": float(form.get("height", 0) or 0),
        "diabetes_duration": float(form.get("diabetes_duration", 0) or 0),
        "hba1c": float(form.get("hba1c", 0) or 0),
        "fasting_blood_sugar": float(form.get("fasting_blood_sugar", 0) or 0),
        "random_blood_sugar": float(form.get("random_blood_sugar", 0) or 0),
        "current_medication": form.get("current_medication", ""),
    }
    symptoms_data = {
        "redness": form.get("redness") == "true",
        "swelling": form.get("swelling") == "true",
        "pain": form.get("pain") == "true",
        "fever": form.get("fever") == "true",
        "numbness": form.get("numbness") == "true",
        "cracks": form.get("cracks") == "true",
        "previous_foot_ulcer": form.get("previous_foot_ulcer") == "true",
        "previous_cellulitis": form.get("previous_cellulitis") == "true",
    }

    patient = Patient(user_id=current_user.id, **patient_data)
    db.session.add(patient)
    db.session.flush()

    symptom_record = Symptom(patient_id=patient.id, **symptoms_data)
    db.session.add(symptom_record)

    left_image = request.files.get("left_image")
    right_image = request.files.get("right_image")
    image_record = Image(patient_id=patient.id)
    if left_image and left_image.filename:
        image_record.left_image = save_upload(left_image)
    if right_image and right_image.filename:
        image_record.right_image = save_upload(right_image)
    db.session.add(image_record)
    db.session.commit()
    return jsonify({"patient": serialize_patient(patient)}), 201


@app.route("/api/predict", methods=["POST"])
@login_required
def predict():
    form = request.form
    patient = Patient.query.get(int(form.get("patient_id", 0) or 0))
    if not patient:
        patient = Patient(user_id=current_user.id, name=form.get("name", "Patient"), age=int(form.get("age", 0) or 0), gender=form.get("gender", "Not specified"))
        db.session.add(patient)
        db.session.flush()
    patient.name = form.get("name", patient.name)
    patient.age = int(form.get("age", patient.age) or patient.age)
    patient.gender = form.get("gender", patient.gender)
    patient.weight = float(form.get("weight", patient.weight) or 0)
    patient.height = float(form.get("height", patient.height) or 0)
    patient.diabetes_duration = float(form.get("diabetes_duration", patient.diabetes_duration) or 0)
    patient.hba1c = float(form.get("hba1c", patient.hba1c) or 0)
    patient.fasting_blood_sugar = float(form.get("fasting_blood_sugar", patient.fasting_blood_sugar) or 0)
    patient.random_blood_sugar = float(form.get("random_blood_sugar", patient.random_blood_sugar) or 0)
    patient.current_medication = form.get("current_medication", patient.current_medication or "")

    symptom_record = patient.symptoms or Symptom(patient_id=patient.id)
    symptom_record.redness = form.get("redness") == "true"
    symptom_record.swelling = form.get("swelling") == "true"
    symptom_record.pain = form.get("pain") == "true"
    symptom_record.fever = form.get("fever") == "true"
    symptom_record.numbness = form.get("numbness") == "true"
    symptom_record.cracks = form.get("cracks") == "true"
    symptom_record.previous_foot_ulcer = form.get("previous_foot_ulcer") == "true"
    symptom_record.previous_cellulitis = form.get("previous_cellulitis") == "true"
    if not patient.symptoms:
        db.session.add(symptom_record)

    image_record = patient.images[-1] if patient.images else Image(patient_id=patient.id)
    left_image = request.files.get("left_image")
    right_image = request.files.get("right_image")
    if left_image and left_image.filename:
        image_record.left_image = save_upload(left_image)
    if right_image and right_image.filename:
        image_record.right_image = save_upload(right_image)
    if not patient.images:
        db.session.add(image_record)

    patient_details = {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "weight": patient.weight,
        "height": patient.height,
        "diabetes_duration": patient.diabetes_duration,
        "hba1c": patient.hba1c,
        "fasting_blood_sugar": patient.fasting_blood_sugar,
        "random_blood_sugar": patient.random_blood_sugar,
        "current_medication": patient.current_medication,
    }
    symptoms_payload = {
        "redness": symptom_record.redness,
        "swelling": symptom_record.swelling,
        "pain": symptom_record.pain,
        "fever": symptom_record.fever,
        "numbness": symptom_record.numbness,
        "cracks": symptom_record.cracks,
        "previous_foot_ulcer": symptom_record.previous_foot_ulcer,
        "previous_cellulitis": symptom_record.previous_cellulitis,
    }
    image_count = int(bool(image_record.left_image)) + int(bool(image_record.right_image))
    prediction_result = predict_condition(patient_details, symptoms_payload, image_count)

    prediction = Prediction(
        patient_id=patient.id,
        prediction=prediction_result["prediction"],
        confidence_score=prediction_result["confidence_score"],
        risk_level=prediction_result["risk_level"],
        recommendation=prediction_result["recommendation"],
    )
    db.session.add(prediction)
    db.session.flush()

    report_path = generate_report(patient, symptom_record, prediction_result, prediction.id)
    report_record = Report(patient_id=patient.id, file_name=os.path.basename(report_path))
    db.session.add(report_record)
    db.session.commit()

    return jsonify({
        "patient": serialize_patient(patient),
        "prediction": prediction_result,
        "report_file": report_record.file_name,
        "prediction_id": prediction.id,
    })


@app.route("/api/reports")
@login_required
def list_reports():
    reports = Report.query.join(Patient).filter(Patient.user_id == current_user.id).order_by(Report.created_at.desc()).all()
    return jsonify({"reports": [serialize_report(r) for r in reports]})


@app.route("/api/reports/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.patient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    return send_from_directory(app.config["REPORT_FOLDER"], report.file_name, as_attachment=True)


@app.route("/api/admin/patients")
@login_required
def admin_patients():
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    search = request.args.get("search", "")
    query = Patient.query
    if search:
        query = query.filter(Patient.name.contains(search))
    patients_list = query.order_by(Patient.created_at.desc()).all()
    return jsonify({"patients": [serialize_patient(p) for p in patients_list]})


@app.route("/api/admin/patients/<int:patient_id>", methods=["DELETE"])
@login_required
def delete_admin_patient(patient_id):
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient deleted"})


@app.route("/api/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/api/patients/<int:patient_id>", methods=["GET", "DELETE"])
@login_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    if request.method == "DELETE":
        db.session.delete(patient)
        db.session.commit()
        return jsonify({"message": "Patient deleted"})
    return jsonify({"patient": serialize_patient(patient)})


def save_upload(file_storage):
    filename = secure_filename(file_storage.filename or "image")
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return unique_name


def generate_report(patient, symptoms, prediction_result, prediction_id):
    filename = f"report_{prediction_id}_{patient.id}.pdf"
    path = os.path.join(app.config["REPORT_FOLDER"], filename)
    pdf = canvas.Canvas(path, pagesize=letter)
    pdf.setTitle("GlucoFoot Sentinel Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(60, 760, "GlucoFoot Sentinel Screening Report")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, 730, f"Patient: {patient.name}")
    pdf.drawString(60, 710, f"Age: {patient.age}")
    pdf.drawString(60, 690, f"Gender: {patient.gender}")
    pdf.drawString(60, 670, f"HbA1c: {patient.hba1c}")
    pdf.drawString(60, 650, f"Fasting Blood Sugar: {patient.fasting_blood_sugar}")
    pdf.drawString(60, 630, f"Random Blood Sugar: {patient.random_blood_sugar}")
    pdf.drawString(60, 610, f"Symptoms: {format_symptoms(symptoms)}")
    pdf.drawString(60, 590, f"Prediction: {prediction_result['prediction']}")
    pdf.drawString(60, 570, f"Confidence: {prediction_result['confidence_score']}")
    pdf.drawString(60, 550, f"Risk Level: {prediction_result['risk_level']}")
    pdf.drawString(60, 530, f"Recommendation: {prediction_result['recommendation']}")
    pdf.drawString(60, 500, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    pdf.drawString(60, 470, "Disclaimer: This application is only a screening support tool and is not a medical diagnosis. Please consult a qualified healthcare professional.")
    pdf.save()
    return path


def format_symptoms(symptoms):
    flags = []
    if symptoms.redness:
        flags.append("Redness")
    if symptoms.swelling:
        flags.append("Swelling")
    if symptoms.pain:
        flags.append("Pain")
    if symptoms.fever:
        flags.append("Fever")
    if symptoms.numbness:
        flags.append("Numbness")
    if symptoms.cracks:
        flags.append("Cracks")
    if symptoms.previous_foot_ulcer:
        flags.append("Previous Foot Ulcer")
    if symptoms.previous_cellulitis:
        flags.append("Previous Cellulitis")
    return ", ".join(flags) or "None"


def serialize_user(user):
    return {"id": user.id, "username": user.username, "email": user.email, "is_admin": user.is_admin}


def serialize_patient(patient):
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "weight": patient.weight,
        "height": patient.height,
        "diabetes_duration": patient.diabetes_duration,
        "hba1c": patient.hba1c,
        "fasting_blood_sugar": patient.fasting_blood_sugar,
        "random_blood_sugar": patient.random_blood_sugar,
        "current_medication": patient.current_medication,
        "symptoms": serialize_symptoms(patient.symptoms),
        "images": [serialize_image(img) for img in patient.images],
        "predictions": [serialize_prediction(pred) for pred in patient.predictions],
        "reports": [serialize_report(report) for report in patient.reports],
    }


def serialize_symptoms(symptoms):
    if not symptoms:
        return {}
    return {
        "redness": symptoms.redness,
        "swelling": symptoms.swelling,
        "pain": symptoms.pain,
        "fever": symptoms.fever,
        "numbness": symptoms.numbness,
        "cracks": symptoms.cracks,
        "previous_foot_ulcer": symptoms.previous_foot_ulcer,
        "previous_cellulitis": symptoms.previous_cellulitis,
    }


def serialize_prediction(prediction):
    return {
        "id": prediction.id,
        "prediction": prediction.prediction,
        "confidence_score": prediction.confidence_score,
        "risk_level": prediction.risk_level,
        "recommendation": prediction.recommendation,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
    }


def serialize_report(report):
    return {"id": report.id, "file_name": report.file_name, "created_at": report.created_at.isoformat() if report.created_at else None}


def serialize_image(image):
    return {"id": image.id, "left_image": image.left_image, "right_image": image.right_image}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
