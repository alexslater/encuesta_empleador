import secrets
from datetime import datetime
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, redirect, url_for, abort, jsonify
from . import db
from .models import ParticipantSession, Interview, Question, Answer

bp_participant = Blueprint("participant", __name__)

def get_session_or_404(token: str) -> ParticipantSession:
    s = ParticipantSession.query.filter_by(token=token).first()
    if not s:
        abort(404)
    return s

@bp_participant.get("/s/<token>")
def start(token):
    s = get_session_or_404(token)
    return render_template("participant/start.html", session=s)

@bp_participant.post("/s/<token>")
def start_post(token):
    s = get_session_or_404(token)
    s.display_name = request.form.get("display_name") or None
    s.org = request.form.get("org") or None
    s.status = "in_progress"
    db.session.commit()
    return redirect(url_for("participant.consent", token=token))

@bp_participant.get("/s/<token>/consent")
def consent(token):
    s = get_session_or_404(token)
    return render_template("participant/consent.html", session=s)

@bp_participant.post("/s/<token>/consent")
def consent_post(token):
    # En MVP basta con registrar que aceptó (podrías guardar un campo consented_at)
    return redirect(url_for("participant.question", token=token, order=1))

@bp_participant.get("/s/<token>/q/<int:order>")
def question(token, order):
    s = get_session_or_404(token)
    q = Question.query.filter_by(interview_id=s.interview_id, order=order).first()
    if not q:
        # No hay más preguntas -> finalizar
        s.status = "submitted"
        s.submitted_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for("participant.done", token=token))

    a = Answer.query.filter_by(session_id=s.id, question_id=q.id).first()
    return render_template("participant/question.html", session=s, question=q, answer=a)

@bp_participant.post("/s/<token>/q/<int:order>/audio")
def upload_audio(token, order):
    s = get_session_or_404(token)
    q = Question.query.filter_by(interview_id=s.interview_id, order=order).first_or_404()

    if "audio" not in request.files:
        return jsonify({"error": "missing audio"}), 400

    f = request.files["audio"]
    if not f.filename:
        f.filename = "recording.webm"

    # Nombre seguro y único
    ext = Path(f.filename).suffix or ".webm"
    filename = f"{s.token}_q{q.order}_{secrets.token_hex(8)}{ext}"
    save_path = Path(current_app.config["UPLOAD_DIR"]) / filename
    f.save(save_path)

    a = Answer.query.filter_by(session_id=s.id, question_id=q.id).first()
    if not a:
        a = Answer(session_id=s.id, question_id=q.id)
        db.session.add(a)

    a.audio_filename = filename
    a.audio_mime = f.mimetype
    # audio_seconds: lo puedes mandar desde frontend (opcional)
    secs = request.form.get("audio_seconds")
    a.audio_seconds = int(secs) if secs and secs.isdigit() else None

    db.session.commit()
    return jsonify({"ok": True, "audio_filename": filename})

@bp_participant.post("/s/<token>/q/<int:order>/text")
def save_text(token, order):
    s = get_session_or_404(token)
    q = Question.query.filter_by(interview_id=s.interview_id, order=order).first_or_404()

    text = (request.form.get("text_answer") or "").strip()

    a = Answer.query.filter_by(session_id=s.id, question_id=q.id).first()
    if not a:
        a = Answer(session_id=s.id, question_id=q.id)
        db.session.add(a)

    a.text_answer = text if text else None
    db.session.commit()
    return redirect(url_for("participant.question", token=token, order=order + 1))

@bp_participant.get("/s/<token>/done")
def done(token):
    s = get_session_or_404(token)
    return render_template("participant/done.html", session=s)
