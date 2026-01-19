import csv
from io import StringIO
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, redirect, url_for, send_file, abort
from . import db
from .models import Interview, Question, ParticipantSession, Answer
from .services import create_invites, create_demo_interview

bp_admin = Blueprint("admin", __name__)

@bp_admin.get("/")
def dashboard():
    interviews = Interview.query.order_by(Interview.created_at.desc()).all()
    sessions = ParticipantSession.query.order_by(ParticipantSession.started_at.desc()).limit(30).all()
    return render_template("admin/dashboard.html", interviews=interviews, sessions=sessions)

@bp_admin.post("/seed")
def seed_demo():
    create_demo_interview()
    return redirect(url_for("admin.dashboard"))

@bp_admin.get("/interviews/new")
def interview_new():
    return render_template("admin/interview_new.html")

@bp_admin.post("/interviews/new")
def interview_new_post():
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not title:
        return "Falta título", 400

    itv = Interview(title=title, description=description or None)
    db.session.add(itv)
    db.session.commit()
    return redirect(url_for("admin.interview_edit", interview_id=itv.id))

@bp_admin.get("/interviews/<int:interview_id>/edit")
def interview_edit(interview_id):
    itv = Interview.query.get_or_404(interview_id)
    questions = Question.query.filter_by(interview_id=itv.id).order_by(Question.order.asc()).all()
    return render_template("admin/interview_edit.html", interview=itv, questions=questions)

@bp_admin.post("/interviews/<int:interview_id>/questions")
def interview_add_question(interview_id):
    itv = Interview.query.get_or_404(interview_id)
    prompt = (request.form.get("prompt") or "").strip()
    if not prompt:
        return redirect(url_for("admin.interview_edit", interview_id=itv.id))

    max_order = db.session.query(db.func.max(Question.order)).filter_by(interview_id=itv.id).scalar() or 0
    q = Question(interview_id=itv.id, order=max_order + 1, prompt=prompt, mode="audio+text")
    db.session.add(q)
    db.session.commit()
    return redirect(url_for("admin.interview_edit", interview_id=itv.id))

@bp_admin.post("/interviews/<int:interview_id>/invite")
def interview_invite(interview_id):
    itv = Interview.query.get_or_404(interview_id)
    n = request.form.get("n") or "5"
    try:
        n = max(1, min(100, int(n)))
    except ValueError:
        n = 5
    create_invites(itv.id, n=n)
    return redirect(url_for("admin.interview_edit", interview_id=itv.id))

@bp_admin.get("/sessions/<int:session_id>")
def session_view(session_id):
    s = ParticipantSession.query.get_or_404(session_id)
    answers = (Answer.query
               .filter_by(session_id=s.id)
               .join(Answer.question)
               .order_by(Question.order.asc())
               .all())
    return render_template("admin/session_view.html", session=s, answers=answers)

@bp_admin.get("/sessions/<int:session_id>/export.csv")
def session_export(session_id):
    s = ParticipantSession.query.get_or_404(session_id)
    answers = (Answer.query
               .filter_by(session_id=s.id)
               .join(Answer.question)
               .order_by(Question.order.asc())
               .all())

    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(["session_id", "token", "participant_name", "org", "question_order", "question", "audio_filename", "text_answer"])
    for a in answers:
        w.writerow([
            s.id, s.token, s.display_name or "", s.org or "",
            a.question.order, a.question.prompt,
            a.audio_filename or "", a.text_answer or ""
        ])

    sio.seek(0)
    return send_file(
        Path(current_app.instance_path) / "tmp_session_export.csv",
        as_attachment=True,
        download_name=f"session_{s.id}.csv",
        mimetype="text/csv"
    )

@bp_admin.get("/uploads/<path:filename>")
def serve_upload(filename):
    # Nota: en producción esto debe ir con auth y/o URLs firmadas
    up = Path(current_app.config["UPLOAD_DIR"]) / filename
    if not up.exists():
        abort(404)
    return send_file(up, as_attachment=False)
