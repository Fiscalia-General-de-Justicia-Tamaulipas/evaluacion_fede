from datetime import datetime, timezone
import os
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from sqlalchemy import (
    create_engine,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    select,
    text,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
    sessionmaker,
)


# ============================================================
# ENV
# ============================================================

for env_path in [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path("/app/.env"),
]:
    if env_path.exists():
        load_dotenv(env_path)
        break


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "La variable DATABASE_URL no está configurada en el archivo .env."
    )


# ============================================================
# BASE SQLALCHEMY
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# MODELOS
# ============================================================

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    options: Mapped[list["Option"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Option.position",
    )


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    letter: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question: Mapped[Question] = relationship(
        back_populates="options"
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    paternal_surname: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    maternal_surname: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id"),
        nullable=False,
    )

    video_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    correct_answers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id"),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    option_id: Mapped[int] = mapped_column(
        ForeignKey("options.id"),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )


# ============================================================
# DATABASE URL
# ============================================================

def get_admin_database_url(database_url: str) -> str:
    parsed = urlparse(database_url)

    database_name = parsed.path.lstrip("/")

    if not database_name:
        return database_url

    admin_parsed = parsed._replace(path="")

    return urlunparse(admin_parsed)


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DATABASE
# ============================================================

def ensure_database_exists() -> None:
    database_name = urlparse(DATABASE_URL).path.lstrip("/")

    if not database_name:
        return

    admin_url = get_admin_database_url(DATABASE_URL)

    admin_engine = create_engine(
        admin_url,
        pool_pre_ping=True,
    )

    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    f"""
                    CREATE DATABASE IF NOT EXISTS `{database_name}`
                    CHARACTER SET utf8mb4
                    COLLATE utf8mb4_unicode_ci
                    """
                )
            )

            connection.commit()

    finally:
        admin_engine.dispose()


def wait_for_database(
    max_attempts: int = 30,
    delay_seconds: int = 2,
) -> None:

    last_error = None

    for attempt in range(max_attempts):

        try:

            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            print("✓ Conexión a MySQL establecida.")
            return

        except Exception as exc:

            last_error = exc

            print(
                f"Esperando MySQL... "
                f"intento {attempt + 1}/{max_attempts}"
            )

            time.sleep(delay_seconds)

    raise RuntimeError(
        "No se pudo conectar a la base de datos MySQL."
    ) from last_error


# ============================================================
# SEED
# ============================================================

def seed() -> None:

    with SessionLocal() as db:

        existing_question = db.scalar(
            select(Question.id).limit(1)
        )

        if existing_question:
            print("✓ Las preguntas ya existen. Seed omitido.")
            return

        print("Insertando preguntas y respuestas...")

        data = [

            (
                1,
                "En qué Ley encontramos los Delitos Electorales.",
                [
                    (
                        "a",
                        "Ley General de Partidos Políticos.",
                        False,
                    ),
                    (
                        "b",
                        "Ley General en Materia de Delitos Electorales.",
                        True,
                    ),
                    (
                        "c",
                        "Ley General de Medios de Impugnación en Materia Electoral.",
                        False,
                    ),
                ],
            ),

            (
                2,
                "Es la Autoridad Electoral encargada de Organizar las elecciones en el Estado de Tamaulipas.",
                [
                    (
                        "a",
                        "Instituto Electoral de Tamaulipas (IETAM).",
                        True,
                    ),
                    (
                        "b",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).",
                        False,
                    ),
                    (
                        "c",
                        "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).",
                        False,
                    ),
                    (
                        "d",
                        "Instituto Nacional Electoral (INE).",
                        False,
                    ),
                ],
            ),

            (
                3,
                "Es la Autoridad Electoral que tiene como principal atribución conocer y resolver los medios de impugnación en materia electoral en el Estado de Tamaulipas.",
                [
                    (
                        "a",
                        "Instituto Electoral de Tamaulipas (IETAM).",
                        False,
                    ),
                    (
                        "b",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).",
                        True,
                    ),
                    (
                        "c",
                        "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).",
                        False,
                    ),
                ],
            ),

            (
                4,
                "Es la Autoridad Electoral que tiene como principal atribución atender e investigar los delitos en materia electoral en el Estado de Tamaulipas.",
                [
                    (
                        "a",
                        "Instituto Electoral de Tamaulipas (IETAM).",
                        False,
                    ),
                    (
                        "b",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).",
                        False,
                    ),
                    (
                        "c",
                        "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).",
                        True,
                    ),
                ],
            ),

            (
                5,
                "Es una de las formas de gobierno en las cuales se ejerce su soberanía eligiendo a sus gobernantes mediante el voto universal, libre y secreto.",
                [
                    (
                        "a",
                        "Democracia",
                        True,
                    ),
                    (
                        "b",
                        "Monarquía",
                        False,
                    ),
                    (
                        "c",
                        "Dictadura",
                        False,
                    ),
                ],
            ),

            (
                6,
                "Es un derecho consagrado en el artículo 35 de la Constitución Política de los Estados Unidos Mexicanos que implica que cada ciudadana o ciudadano puede participar en elegir a sus representantes al emitir su voto. Este derecho va más allá de la elección de representantes y también se ejerce a través de otros mecanismos participativos de la democracia, tales como las consultas populares.",
                [
                    (
                        "a",
                        "Voto activo.",
                        True,
                    ),
                    (
                        "b",
                        "Voto pasivo.",
                        False,
                    ),
                ],
            ),

            (
                7,
                "El derecho de solicitar el registro de candidatos ante la autoridad electoral corresponde a los partidos políticos, así como a los ciudadanos que soliciten su registro de manera independiente y cumplan con los requisitos, condiciones y términos que determine la legislación, este derecho consagrado en el numeral 35 de la Constitución Política de los Estados Unidos Mexicanos se le conoce como:",
                [
                    (
                        "a",
                        "Voto activo.",
                        False,
                    ),
                    (
                        "b",
                        "Voto pasivo.",
                        True,
                    ),
                ],
            ),

            (
                8,
                "Es el conjunto de actos realizados en fases y que la Constitución y la Ley General de Instituciones y Procedimientos Electorales mandatan a las autoridades electorales, los partidos políticos y los ciudadanos para renovar periódicamente a los integrantes de los Poderes Legislativos y Ejecutivo federal y de las entidades federativas, así como de los ayuntamientos en los estados de la República y de las alcaldías en la Ciudad de México.",
                [
                    (
                        "a",
                        "Proceso Legislativo.",
                        False,
                    ),
                    (
                        "b",
                        "Proceso Electoral.",
                        True,
                    ),
                    (
                        "c",
                        "Proceso Penal.",
                        False,
                    ),
                ],
            ),

            (
                9,
                "Son los comicios federal y local, que coinciden exactamente en la fecha prefijada en la Legislación Electoral de un Estado y en la Ley General de Instituciones y Procedimientos Electorales, en este tipo de proceso electoral se eligen cargos de elección popular locales y federales.",
                [
                    (
                        "a",
                        "Proceso electoral extraordinario.",
                        False,
                    ),
                    (
                        "b",
                        "Proceso electoral ordinario.",
                        False,
                    ),
                    (
                        "c",
                        "Proceso electoral concurrente.",
                        True,
                    ),
                ],
            ),

            (
                10,
                "Es el periodo que comprende los tres días previos a la Jornada Electoral y concluye con la clausura de las casillas durante este periodo no está permitido realizar actos públicos de campaña, propaganda o proselitismo electoral publicar y difundir propaganda gubernamental.",
                [
                    (
                        "a",
                        "Precampaña",
                        False,
                    ),
                    (
                        "b",
                        "Veda electoral",
                        True,
                    ),
                    (
                        "c",
                        "Campaña",
                        False,
                    ),
                ],
            ),
        ]

        for number, question_text, options in data:

            question = Question(
                number=number,
                text=question_text,
            )

            db.add(question)

            db.flush()

            for position, (
                letter,
                option_text,
                correct,
            ) in enumerate(options, start=1):

                db.add(
                    Option(
                        question_id=question.id,
                        letter=letter,
                        text=option_text,
                        is_correct=correct,
                        position=position,
                    )
                )

        db.commit()

        print("✓ Preguntas y opciones insertadas correctamente.")


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database() -> None:

    print("Inicializando base de datos...")

    ensure_database_exists()

    wait_for_database()

    print("Creando tablas...")

    Base.metadata.create_all(bind=engine)

    print("✓ Tablas verificadas/creadas.")

    seed()

    print("✓ Base de datos inicializada correctamente.")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Evaluación FEDE - FGJ Tamaulipas",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5174",
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    initialize_database()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# SCHEMAS
# ============================================================

class ParticipantIn(BaseModel):

    first_name: str = Field(
        min_length=2,
        max_length=120,
    )

    paternal_surname: str = Field(
        min_length=2,
        max_length=120,
    )

    maternal_surname: str = Field(
        min_length=2,
        max_length=120,
    )


class StartIn(ParticipantIn):

    video_completed: bool = False


class AnswerIn(BaseModel):

    question_id: int
    option_id: int


class FinishIn(BaseModel):

    answers: list[AnswerIn] = Field(
        min_length=10,
        max_length=10,
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
    }


# ============================================================
# QUESTIONS
# ============================================================

@app.get("/api/questions")
def questions(
    db: Session = Depends(get_db),
):

    qs = db.scalars(
        select(Question)
        .order_by(Question.number)
    ).all()

    return [
        {
            "id": q.id,
            "number": q.number,
            "text": q.text,
            "options": [
                {
                    "id": o.id,
                    "letter": o.letter,
                    "text": o.text,
                }
                for o in q.options
            ],
        }
        for q in qs
    ]


# ============================================================
# START EVALUATION
# ============================================================

@app.post("/api/evaluations/start")
def start(
    data: StartIn,
    db: Session = Depends(get_db),
):

    participant = Participant(
        first_name=data.first_name.strip(),
        paternal_surname=data.paternal_surname.strip(),
        maternal_surname=data.maternal_surname.strip(),
    )

    db.add(participant)

    db.flush()

    total_questions = db.query(Question).count()

    evaluation = Evaluation(
        participant_id=participant.id,
        video_completed=data.video_completed,
        started_at=datetime.now(timezone.utc),
        total_questions=total_questions,
    )

    db.add(evaluation)

    db.commit()

    db.refresh(evaluation)

    return {
        "evaluation_id": evaluation.id,
        "participant_id": participant.id,
    }


# ============================================================
# VIDEO COMPLETED
# ============================================================

@app.post(
    "/api/evaluations/{evaluation_id}/video-completed"
)
def video_completed(
    evaluation_id: int,
    db: Session = Depends(get_db),
):

    evaluation = db.get(
        Evaluation,
        evaluation_id,
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada.",
        )

    evaluation.video_completed = True

    db.commit()

    return {
        "video_completed": True,
    }


# ============================================================
# FINISH
# ============================================================

@app.post(
    "/api/evaluations/{evaluation_id}/finish"
)
def finish(
    evaluation_id: int,
    data: FinishIn,
    db: Session = Depends(get_db),
):

    evaluation = db.get(
        Evaluation,
        evaluation_id,
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada.",
        )

    if not evaluation.video_completed:

        raise HTTPException(
            status_code=400,
            detail=(
                "El video debe haberse completado "
                "antes de contestar la evaluación."
            ),
        )

    if evaluation.completed_at:

        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    questions_list = db.scalars(
        select(Question)
        .order_by(Question.number)
    ).all()

    if len(data.answers) != len(questions_list):

        raise HTTPException(
            status_code=400,
            detail="Debes responder todas las preguntas.",
        )

    correct = 0

    # Evita enviar dos respuestas para la misma pregunta
    submitted_questions = set()

    for item in data.answers:

        if item.question_id in submitted_questions:

            raise HTTPException(
                status_code=400,
                detail="No puedes responder una pregunta más de una vez.",
            )

        submitted_questions.add(item.question_id)

        question = db.get(
            Question,
            item.question_id,
        )

        option = db.get(
            Option,
            item.option_id,
        )

        if not question or not option:

            raise HTTPException(
                status_code=400,
                detail="Respuesta inválida.",
            )

        if option.question_id != question.id:

            raise HTTPException(
                status_code=400,
                detail="La opción no pertenece a la pregunta seleccionada.",
            )

        is_correct = bool(option.is_correct)

        if is_correct:
            correct += 1

        answer = Answer(
            evaluation_id=evaluation.id,
            question_id=question.id,
            option_id=option.id,
            is_correct=is_correct,
        )

        db.add(answer)

    total = len(questions_list)

    score = (
        round((correct / total) * 100)
        if total
        else 0
    )

    evaluation.correct_answers = correct
    evaluation.total_questions = total
    evaluation.score = score
    evaluation.completed_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "success": True,
        "message": "Evaluación registrada correctamente.",
    }