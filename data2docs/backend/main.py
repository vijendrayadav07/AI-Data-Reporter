from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Import your AI + report functions
from chat_with_groq import chat_with_groq
from report_gen import save_insights_to_html, generate_pdf

app = Flask(__name__)

# ---- Config ----
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://Vijendra:12%21%40Vijendra@localhost/ai_data_reporter"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ---- Models ----
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    reports = db.relationship("Report", backref="owner", lazy=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    pdf_path = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ---- Routes ----
@app.route("/")
def home():
    return "✅ Flask API is running"

# --- Auth ---
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=user.username)
    return jsonify(access_token=token, username=user.username, email=user.email)

# --- Reports CRUD ---
@app.route('/reports', methods=['GET', 'POST'])
@jwt_required()
def handle_reports():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if request.method == 'POST':
        data = request.get_json()
        new_report = Report(
            title=data["title"],
            content=data["content"],
            pdf_path=data.get("pdf_path"),
            user_id=user.id
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify({"message": "Report created"}), 201

    reports = Report.query.filter_by(user_id=user.id).all()
    return jsonify([
        {"id": r.id, "title": r.title, "content": r.content, "pdf_path": r.pdf_path}
        for r in reports
    ])

@app.route('/reports/<int:report_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_report(report_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    report = Report.query.filter_by(id=report_id, user_id=user.id).first()

    if not report:
        return jsonify({"error": "Report not found"}), 404

    if request.method == 'PUT':
        data = request.get_json()
        report.title = data.get("title", report.title)
        report.content = data.get("content", report.content)
        report.pdf_path = data.get("pdf_path", report.pdf_path)
        db.session.commit()
        return jsonify({"message": "Report updated"})

    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Report deleted"})

# --- AI Insights Endpoint ---
@app.route('/generate-insights', methods=['POST'])
@jwt_required()
def generate_insights():
    data = request.get_json()
    dataset_stats = data.get("stats", "")
    if not dataset_stats:
        return jsonify({"error": "Stats missing"}), 400

    insights = chat_with_groq([
        {"role": "system", "content": "You're a senior data analyst. Provide 5–7 insights:"},
        {"role": "user", "content": dataset_stats}
    ])
    return jsonify({"insights": insights})

# --- Save Report (Generate PDF) ---
@app.route('/save-report', methods=['POST'])
@jwt_required()
def save_report():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    data = request.get_json()
    insights = data.get("insights", "")
    if not insights:
        return jsonify({"error": "Insights missing"}), 400

    html_path = save_insights_to_html(insights)
    pdf_path = generate_pdf(html_path)

    new_report = Report(
        title=data.get("title", "AI Report"),
        content=insights,
        pdf_path=pdf_path,
        user_id=user.id
    )
    db.session.add(new_report)
    db.session.commit()

    return jsonify({"message": "Report saved", "pdf_path": pdf_path})

# ---- Init DB + Run ----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
