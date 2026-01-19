from datetime import datetime
from . import db

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship("Question", backref="interview", cascade="all, delete-orphan")
    sessions = db.relationship("ParticipantSession", backref="interview", cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(20), default="audio+text")  # audio | text | audio+text

class ParticipantSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    display_name = db.Column(db.String(140), nullable=True)
    org = db.Column(db.String(140), nullable=True)

    status = db.Column(db.String(20), default="started")  # started, in_progress, submitted
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)

    answers = db.relationship("Answer", backref="session", cascade="all, delete-orphan")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("participant_session.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)

    audio_filename = db.Column(db.String(255), nullable=True)
    audio_mime = db.Column(db.String(80), nullable=True)
    audio_seconds = db.Column(db.Integer, nullable=True)

    text_answer = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship("Question")
