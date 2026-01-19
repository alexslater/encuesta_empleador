import secrets
from datetime import datetime
from . import db
from .models import Interview, Question, ParticipantSession

def gen_token(nbytes: int = 16) -> str:
    return secrets.token_urlsafe(nbytes)

def create_demo_interview() -> Interview:
    """
    Crea una entrevista demo si no existe ninguna.
    Útil para arrancar el MVP en 2 minutos.
    """
    existing = Interview.query.first()
    if existing:
        return existing

    itv = Interview(
        title="Piloto Tredu - Feedback Empleadores",
        description="Entrevista breve (audio-first). Responde con ejemplos concretos."
    )
    db.session.add(itv)
    db.session.flush()

    prompts = [
        "Cuéntanos tu rol y el tipo de profesionales que sueles contratar.",
        "¿Cuáles son 3 habilidades clave (técnicas o transversales) que hoy más te cuesta encontrar?",
        "Describe un caso real de buen desempeño (¿qué hizo esa persona?).",
        "¿Qué señales o evidencias te gustaría ver en un egresado (portafolio, proyectos, certificaciones)?",
        "Si pudieras cambiar 1 cosa en la formación de pregrado, ¿cuál sería y por qué?"
    ]
    for i, p in enumerate(prompts, start=1):
        db.session.add(Question(interview_id=itv.id, order=i, prompt=p, mode="audio+text"))

    db.session.commit()
    return itv

def create_invites(interview_id: int, n: int = 5):
    invites = []
    for _ in range(n):
        token = gen_token()
        s = ParticipantSession(interview_id=interview_id, token=token, status="started", started_at=datetime.utcnow())
        db.session.add(s)
        invites.append(s)
    db.session.commit()
    return invites
