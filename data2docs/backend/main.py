# backend/main.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import math

def sanitize_for_json(data):
    """
    Converts NaN or Infinity values to 0 so JSON is valid.
    Works recursively for dicts and lists.
    """
    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return 0.0
        return data
    elif isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(v) for v in data]
    return data

app = Flask(__name__)

# ----------------- CONFIG -----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://Vijendra:12%21%40Vijendra@localhost/ai_data_reporter"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ----------------- MODELS -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ----------------- ROUTES -----------------
@app.route("/")
def home():
    return jsonify(sanitize_for_json({"message": "Flask server is running 🚀"})), 200

# -------- SIGNUP --------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify(sanitize_for_json({"error": "Invalid request"})), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify(sanitize_for_json({"error": "User already exists"})), 400

    hashed_pw = generate_password_hash(data["password"])
    new_user = User(username=data["username"], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(sanitize_for_json({"message": "User created"})), 201

# -------- LOGIN --------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify(sanitize_for_json({"error": "Invalid request"})), 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify(sanitize_for_json({"error": "Invalid credentials"})), 401

    token = create_access_token(identity=user.username)
    return jsonify(sanitize_for_json({"access_token": token})), 200

# -------- REPORTS --------
@app.route('/reports', methods=['GET', 'POST'])
@jwt_required()
def handle_reports():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if request.method == 'POST':
        data = request.get_json()
        if not data or "title" not in data or "content" not in data:
            return jsonify(sanitize_for_json({"error": "Invalid request"})), 400
        new_report = Report(title=data["title"], content=data["content"], user_id=user.id)
        db.session.add(new_report)
        db.session.commit()
        return jsonify(sanitize_for_json({"message": "Report created"})), 201

    reports = Report.query.filter_by(user_id=user.id).all()
    reports_data = [{"id": r.id, "title": r.title, "content": r.content} for r in reports]
    return jsonify(sanitize_for_json(reports_data)), 200

# -------- MODIFY REPORT --------
@app.route('/reports/<int:report_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_report(report_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    report = Report.query.filter_by(id=report_id, user_id=user.id).first()

    if not report:
        return jsonify(sanitize_for_json({"error": "Report not found"})), 404

    if request.method == 'PUT':
        data = request.get_json()
        report.title = data.get("title", report.title)
        report.content = data.get("content", report.content)
        db.session.commit()
        return jsonify(sanitize_for_json({"message": "Report updated"})), 200

    db.session.delete(report)
    db.session.commit()
    return jsonify(sanitize_for_json({"message": "Report deleted"})), 200

# ----------------- RUN -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create tables if not exist
    app.run(debug=True, port=5000)
