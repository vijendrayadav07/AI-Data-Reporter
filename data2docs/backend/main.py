# backend/main.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

import math
import os

# ----------------- HELPER -----------------
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

# ----------------- APP & CONFIG -----------------
app = Flask(__name__)
CORS(app)

# Get DB URL from environment
db_url = os.environ.get("DATABASE_URL")

# Render gives postgres:// but SQLAlchemy needs postgresql+psycopg2://
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

# Use fallback for local dev if no DATABASE_URL set
app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "postgresql+psycopg2://ai_data_reporter_db_user:9tqOuaB57A5gh7Zxw3FTpyjhbOD@dpg-d2k4qf63jp1c73fqh62g-a.oregon-postgres.render.com/ai_data_reporter_db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("FLASK_JWT_SECRET_KEY", "supersecretkey")

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ----------------- MODELS -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ----------------- API PREFIX -----------------
API_PREFIX = "/api"
##

# ----------------- ROUTES -----------------
@app.route("/")
def home():
    return {"message": "Backend is running!"}

@app.route(f"{API_PREFIX}/", methods=["GET"])
def api_home():
    return jsonify(sanitize_for_json({"message": "Flask server is running 🚀"})), 200

@app.route(f"{API_PREFIX}/signup", methods=["POST"])
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

@app.route(f"{API_PREFIX}/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify(sanitize_for_json({"error": "Invalid request"})), 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify(sanitize_for_json({"error": "Invalid credentials"})), 401

    token = create_access_token(identity=user.username)
    return jsonify(sanitize_for_json({"access_token": token})), 200

@app.route(f"{API_PREFIX}/reports", methods=["GET", "POST"])
@jwt_required()
def handle_reports():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if request.method == "POST":
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

@app.route(f"{API_PREFIX}/reports/<int:report_id>", methods=["PUT", "DELETE"])
@jwt_required()
def modify_report(report_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    report = Report.query.filter_by(id=report_id, user_id=user.id).first()

    if not report:
        return jsonify(sanitize_for_json({"error": "Report not found"})), 404

    if request.method == "PUT":
        data = request.get_json()
        report.title = data.get("title", report.title)
        report.content = data.get("content", report.content)
        db.session.commit()
        return jsonify(sanitize_for_json({"message": "Report updated"})), 200

    db.session.delete(report)
    db.session.commit()
    return jsonify(sanitize_for_json({"message": "Report deleted"})), 200

# ----------------- DB INIT -----------------
@app.before_first_request
def create_tables():
    """Ensure tables exist (important for Render deployment)."""
    db.create_all()

# ----------------- RUN -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # local dev
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
