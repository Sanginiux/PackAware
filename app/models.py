from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)
    recyclable = db.Column(db.Boolean, default=False)
    pollution_score = db.Column(db.Float)
    eco_score = db.Column(db.Float)
    disposal_tips = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_by = db.Column(db.String(100))

class QuizScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(100))
    score = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
