from models import User
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password):
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return True
    return False
