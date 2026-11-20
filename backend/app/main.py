from __future__ import annotations

import json
import hashlib
import re
from html import escape
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import SystemRandom, compare_digest, token_urlsafe
from urllib.parse import urlencode
from urllib.request import Request as URLRequest, urlopen
from urllib.error import URLError, HTTPError
from uuid import uuid4

from dotenv import load_dotenv

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from passlib.context import CryptContext
from jose import JWTError, jwt

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    inspect,
    select,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.exc import IntegrityError


# ============================================================
# ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR.parent.parent / ".env")
load_dotenv("/app/.env")


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@db:3306/evaluacion_fede",
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "",
).strip()

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)

MAIL_HOST = os.getenv("MAIL_HOST", "").strip()
MAIL_JWT = os.getenv("MAIL_JWT", "").strip().strip('"').strip("'")
MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS", "").strip().strip('"').strip("'")
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",")[0],
).strip().rstrip("/")
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))


def score_percentage(value: int | None) -> int | None:
    if value is None:
        return None
    return int(value)


def evaluation_percentage(evaluation: Evaluation) -> int | None:
    if evaluation.correct_answers is not None and evaluation.total_questions > 0:
        return round(
            (evaluation.correct_answers / evaluation.total_questions) * 100
        )
    return score_percentage(evaluation.score)


PASSING_SCORE = 70
QUESTIONS_PER_EXAM = 10
COURSE_KEY = "delitos-electorales-investigacion-sistema-electoral-mexicano"
COURSE_NAME = "Delitos Electorales y su investigación en el Sistema Electoral Mexicano"
COURSE_MODULE_IDS = (1, 2, 3)


# ============================================================
# DATABASE
# ============================================================

def get_admin_database_url() -> str:
    """
    Construye una URL apuntando a la base administrativa de MySQL
    para poder crear la BD si todavía no existe.
    """

    url = DATABASE_URL

    if "/" not in url.split("://", 1)[-1]:
        return url

    prefix, remainder = url.split("://", 1)

    credentials_host, _, database = remainder.rpartition("/")

    if not database:
        return url

    return f"{prefix}://{credentials_host}/"


def ensure_database_exists() -> None:
    """
    Crea la base de datos si no existe.
    """

    try:
        admin_url = get_admin_database_url()

        database_name = DATABASE_URL.rsplit("/", 1)[-1]

        if "?" in database_name:
            database_name = database_name.split("?", 1)[0]

        engine_admin = create_engine(
            admin_url,
            pool_pre_ping=True,
        )

        with engine_admin.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "CHARACTER SET utf8mb4 "
                    "COLLATE utf8mb4_unicode_ci"
                )
            )

        engine_admin.dispose()

    except Exception as exc:
        print(
            "No se pudo verificar/crear la base de datos:",
            exc,
        )


def wait_for_database(
    attempts: int = 30,
    delay: int = 2,
) -> None:
    """
    Espera hasta que MySQL esté disponible.
    """

    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            print("Base de datos disponible.")
            return

        except Exception as exc:
            print(
                f"Esperando base de datos "
                f"({attempt}/{attempts}): {exc}"
            )

            time.sleep(delay)

    raise RuntimeError(
        "No fue posible conectar con la base de datos."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ============================================================
# BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# MODELOS DE CATÁLOGOS
# ============================================================

class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    municipalities: Mapped[list["Municipality"]] = relationship(
        back_populates="state",
        cascade="all, delete-orphan",
    )


class Municipality(Base):
    __tablename__ = "municipalities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    state_id: Mapped[int] = mapped_column(
        ForeignKey("states.id"),
        nullable=False,
        index=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_other: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    state: Mapped["State"] = relationship(
        back_populates="municipalities",
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="municipality",
    )

    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_municipality_code",
        ),
    )


class Gender(Base):
    __tablename__ = "genders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="gender",
    )


class AgeRange(Base):
    __tablename__ = "age_ranges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="age_range",
    )


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="occupation",
    )


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="sector",
    )


class YesNoOption(Base):
    __tablename__ = "yes_no_options"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )


class EducationLevel(Base):
    __tablename__ = "education_levels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="education_level",
    )


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    paternal_surname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    maternal_surname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    curp: Mapped[str] = mapped_column(
        String(18),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # --------------------------------------------------------
    # Municipio
    # --------------------------------------------------------

    municipality_id: Mapped[int | None] = mapped_column(
        ForeignKey("municipalities.id"),
        nullable=True,
    )

    municipality_other: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    municipality_other_state: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # --------------------------------------------------------
    # Género
    # --------------------------------------------------------

    gender_id: Mapped[int | None] = mapped_column(
        ForeignKey("genders.id"),
        nullable=True,
    )

    gender_other: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # --------------------------------------------------------
    # Edad
    # --------------------------------------------------------

    age_range_id: Mapped[int | None] = mapped_column(
        ForeignKey("age_ranges.id"),
        nullable=True,
    )

    # --------------------------------------------------------
    # Ocupación
    # --------------------------------------------------------

    occupation_id: Mapped[int | None] = mapped_column(
        ForeignKey("occupations.id"),
        nullable=True,
    )

    occupation_other: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # --------------------------------------------------------
    # Sector
    # --------------------------------------------------------

    sector_id: Mapped[int | None] = mapped_column(
        ForeignKey("sectors.id"),
        nullable=True,
    )

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------

    indigenous_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"),
        nullable=True,
    )

    afro_mexican_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"),
        nullable=True,
    )

    disability_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"),
        nullable=True,
    )

    lgbtttiq_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"),
        nullable=True,
    )

    education_level_id: Mapped[int | None] = mapped_column(
        ForeignKey("education_levels.id"),
        nullable=True,
    )

    # --------------------------------------------------------
    # Relaciones
    # --------------------------------------------------------

    municipality: Mapped["Municipality | None"] = relationship(
        back_populates="users",
    )

    gender: Mapped["Gender | None"] = relationship(
        back_populates="users",
    )

    age_range: Mapped["AgeRange | None"] = relationship(
        back_populates="users",
    )

    occupation: Mapped["Occupation | None"] = relationship(
        back_populates="users",
    )

    sector: Mapped["Sector | None"] = relationship(
        back_populates="users",
    )

    education_level: Mapped[
        "EducationLevel | None"
    ] = relationship(
        back_populates="users",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return " ".join(
            part
            for part in [
                self.first_name,
                self.paternal_surname,
                self.maternal_surname,
            ]
            if part
        ).strip()


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, index=True)


class AuthSecurityState(Base):
    __tablename__ = "auth_security_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "scope",
            "identifier",
            name="uq_auth_security_scope_identifier",
        ),
    )


# ============================================================
# PREGUNTAS
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
        nullable=False,
    )

    module_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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

    __table_args__ = (
        UniqueConstraint(
            "module_id",
            "number",
            name="uq_question_module_number",
        ),
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
        String(5),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    question: Mapped["Question"] = relationship(
        back_populates="options",
    )


# ============================================================
# EVALUACIÓN
# ============================================================

class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="evaluations",
    )

    module_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
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

    # Índice 0-based de la pregunta actual.
    current_question: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    question_order: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    active_attempt_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
    )

    video_session_nonce: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    video_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    course_key: Mapped[str] = mapped_column(String(100), nullable=False)
    folio: Mapped[str] = mapped_column(String(48), nullable=False)
    user_name: Mapped[str] = mapped_column(String(320), nullable=False)

    module_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    evaluation_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluations.id"),
        nullable=True,
        unique=True,
    )

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "course_key", name="uq_certificate_user_course"),
        UniqueConstraint("folio", name="uq_certificate_folio"),
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

    evaluation: Mapped["Evaluation"] = relationship(
        back_populates="answers",
    )

    __table_args__ = (
        UniqueConstraint(
            "evaluation_id",
            "question_id",
            name="uq_answer_evaluation_question",
        ),
    )


# ============================================================
# SEEDS
# ============================================================

TAMAULIPAS_MUNICIPALITIES = [
    "Abasolo",
    "Aldama",
    "Altamira",
    "Antiguo Morelos",
    "Burgos",
    "Bustamante",
    "Camargo",
    "Casas",
    "Ciudad Madero",
    "Cruillas",
    "Gómez Farías",
    "González",
    "Guerrero",
    "Gustavo Díaz Ordaz",
    "Güémez",
    "Hidalgo",
    "Jaumave",
    "Jiménez",
    "Llera",
    "Mainero",
    "El Mante",
    "Matamoros",
    "Méndez",
    "Mier",
    "Miguel Alemán",
    "Miquihuana",
    "Nuevo Laredo",
    "Nuevo Morelos",
    "Ocampo",
    "Padilla",
    "Palmillas",
    "Reynosa",
    "Río Bravo",
    "San Carlos",
    "San Fernando",
    "San Nicolás",
    "Soto la Marina",
    "Tampico",
    "Tula",
    "Valle Hermoso",
    "Victoria",
    "Villagrán",
    "Xicoténcatl",
]


GENDER_NAMES = [
    "Femenino",
    "Masculino",
    "No binario",
    "Prefiero no contestar",
    "Otro",
]


AGE_RANGE_NAMES = [
    "Menor de 18",
    "De 18 a 25",
    "De 26 a 30",
    "De 31 a 35",
    "De 36 a 40",
    "De 41 a 50",
    "De 51 a 60",
    "Más de 61",
]


SECTOR_NAMES = [
    "Fiscalías",
    "Secretaría de Seguridad Pública",
    "Secretaría de la Defensa Nacional",
    "Instituto Nacional Electoral",
    "Institutos Electorales",
    "Servidor Público",
    "Funcionario de Casilla",
    "Comunidad Estudiantil",
    "Público en General",
]


YES_NO_NAMES = [
    "Sí",
    "No",
]


EDUCATION_LEVEL_NAMES = [
    "Básico",
    "Técnico",
    "Medio Superior",
    "Licenciatura",
    "Especialidad",
    "Maestría",
    "Doctorado",
    "No aplica",
]


OCCUPATION_NAMES = [
    "Abogado(a)",
    "Administrador(a)",
    "Agricultor(a)",
    "Albañil",
    "Analista",
    "Arquitecto(a)",
    "Artesano(a)",
    "Artista",
    "Asistente administrativo(a)",
    "Auditor(a)",
    "Comerciante",
    "Contador(a)",
    "Consultor(a)",
    "Cocinero(a)",
    "Diseñador(a)",
    "Docente",
    "Economista",
    "Electricista",
    "Enfermero(a)",
    "Estudiante",
    "Farmacéutico(a)",
    "Fisioterapeuta",
    "Fotógrafo(a)",
    "Funcionario(a) público(a)",
    "Ganadero(a)",
    "Ingeniero(a)",
    "Investigador(a)",
    "Jornalero(a)",
    "Maestro(a)",
    "Médico(a)",
    "Mesero(a)",
    "Militar",
    "Músico(a)",
    "Odontólogo(a)",
    "Operador(a)",
    "Paramédico(a)",
    "Periodista",
    "Policía",
    "Programador(a)",
    "Psicólogo(a)",
    "Químico(a)",
    "Recepcionista",
    "Recursos humanos",
    "Secretaria(o)",
    "Sociólogo(a)",
    "Técnico(a)",
    "Trabajador(a) social",
    "Transportista",
    "Vendedor(a)",
    "Veterinario(a)",
    "Empresario(a)",
    "Empleado(a) administrativo(a)",
    "Empleado(a) de comercio",
    "Empleado(a) de servicios",
    "Trabajador(a) independiente",
    "Ama/o de casa",
    "Jubilado(a)",
    "Pensionado(a)",
    "Desempleado(a)",
    "Otro",
]


# ============================================================
# SEED HELPERS
# ============================================================

def seed_catalog_simple(
    db: Session,
    model,
    names: list[str],
) -> None:
    existing = {
        name
        for name in db.scalars(
            select(model.name)
        ).all()
    }

    changed = False

    for name in names:
        if name not in existing:
            db.add(
                model(name=name)
            )
            changed = True

    if changed:
        db.commit()


def seed_profile_catalogs() -> None:
    with SessionLocal() as db:

        # ----------------------------------------------------
        # Estado
        # ----------------------------------------------------

        tamaulipas = db.scalar(
            select(State)
            .where(State.name == "Tamaulipas")
        )

        if not tamaulipas:
            tamaulipas = State(
                name="Tamaulipas"
            )

            db.add(tamaulipas)
            db.commit()
            db.refresh(tamaulipas)

        # ----------------------------------------------------
        # Municipios
        # ----------------------------------------------------

        existing_municipalities = {
            name
            for name in db.scalars(
                select(Municipality.name)
                .where(
                    Municipality.state_id ==
                    tamaulipas.id
                )
            ).all()
        }

        for municipality_name in TAMAULIPAS_MUNICIPALITIES:
            if municipality_name not in existing_municipalities:
                db.add(
                    Municipality(
                        state_id=tamaulipas.id,
                        name=municipality_name,
                        is_other=False,
                    )
                )

        db.commit()

        # ----------------------------------------------------
        # Catálogos
        # ----------------------------------------------------

        seed_catalog_simple(
            db,
            Gender,
            GENDER_NAMES,
        )

        seed_catalog_simple(
            db,
            AgeRange,
            AGE_RANGE_NAMES,
        )

        seed_catalog_simple(
            db,
            Occupation,
            OCCUPATION_NAMES,
        )

        seed_catalog_simple(
            db,
            Sector,
            SECTOR_NAMES,
        )

        seed_catalog_simple(
            db,
            YesNoOption,
            YES_NO_NAMES,
        )

        seed_catalog_simple(
            db,
            EducationLevel,
            EDUCATION_LEVEL_NAMES,
        )


# ============================================================
# PREGUNTAS
# ============================================================

def seed_questions() -> None:
    """
    Inserta el banco inicial solo cuando está vacío; no reemplaza preguntas existentes.
    """

    with SessionLocal() as db:

        count = db.scalar(
            select(text("COUNT(*)"))
            .select_from(Question)
        )

        if int(count or 0) > 0:
            return

        questions_data = [
            {
                "number": 1,
                "text": (
                    "¿Cuál es la característica del voto que implica que "
                    "todo ciudadano debe votar de acuerdo con su preferencia "
                    "política, o en favor del candidato, candidata o partido "
                    "político que elija sin coacción o presión de ningún tipo?"
                ),
                "options": [
                    ("A", "Universal", False),
                    ("B", "Voto libre", True),
                    ("C", "Intransferible", False),
                ],
            },
            {
                "number": 2,
                "text": (
                    "¿Cuál es la Autoridad Electoral encargada de organizar "
                    "las elecciones federales?"
                ),
                "options": [
                    ("A", "Instituto Electoral de Tamaulipas (IETAM)", False),
                    (
                        "B",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                        False,
                    ),
                    (
                        "C",
                        "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE)",
                        False,
                    ),
                    ("D", "Instituto Nacional Electoral (INE)", True),
                ],
            },
            {
                "number": 3,
                "text": (
                    "¿Cuál es la Autoridad Electoral que tiene como principales "
                    "atribuciones, resolver las impugnaciones y controversias "
                    "sobre elecciones federales así como realizar el cómputo "
                    "final, calificar la legalidad y declarar al presidente "
                    "electo de México?"
                ),
                "options": [
                    (
                        "A",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                        False,
                    ),
                    (
                        "B",
                        "Fiscalía Especializada en Materia de Delitos Electorales de la FGR (FISEL)",
                        False,
                    ),
                    (
                        "C",
                        "Tribunal Electoral del Poder Judicial de la Federación (TEPJF)",
                        True,
                    ),
                ],
            },
            {
                "number": 4,
                "text": (
                    "Es la Autoridad Electoral que tiene como principal "
                    "atribución atender e investigar los delitos en materia "
                    "electoral del fuero federal."
                ),
                "options": [
                    (
                        "A",
                        "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                        False,
                    ),
                    (
                        "B",
                        "Fiscalía Especializada en Materia de Delitos Electorales de la Fiscalía General de la República (FGR)",
                        True,
                    ),
                    (
                        "C",
                        "Fiscalía Especializada en Delitos Electorales de la Fiscalía General de Justicia del Estado de Tamaulipas (FEDE)",
                        False,
                    ),
                ],
            },
            {
                "number": 5,
                "text": (
                    "¿Cuál de los siguientes cargos de elección popular no "
                    "corresponde a un proceso electoral local?"
                ),
                "options": [
                    ("A", "Gobernador.", False),
                    ("B", "Alcaldes y Regidurías.", False),
                    ("C", "Presidente de la República.", True),
                    ("D", "Diputado Local.", False),
                ],
            },
            {
                "number": 6,
                "text": (
                    "¿A qué mecanismo de protección de la democracia pertenecen "
                    "las Fiscalías Especializadas en Delitos Electorales?"
                ),
                "options": [
                    ("A", "Mecanismos Administrativos.", False),
                    ("B", "Mecanismos Jurisdiccionales.", False),
                    ("C", "Mecanismos de Procuración de Justicia.", True),
                ],
            },
            {
                "number": 7,
                "text": (
                    "Es la herramienta mediante la cual se ejerce la democracia, "
                    "y es el pueblo en su conjunto quien ejerce su soberanía "
                    "eligiendo a sus gobernantes mediante elecciones periódicas."
                ),
                "options": [
                    ("A", "El derecho de huelga.", False),
                    ("B", "El voto.", True),
                    ("C", "La consulta popular.", False),
                ],
            },
            {
                "number": 8,
                "text": (
                    "Es la característica del voto que consiste en que cada "
                    "ciudadano o ciudadana debe votar sin ser observado u observada."
                ),
                "options": [
                    ("A", "Personal.", False),
                    ("B", "Libre.", False),
                    ("C", "Secreto.", True),
                ],
            },
            {
                "number": 9,
                "text": (
                    "Es el tipo de Proceso Electoral, mediante el cual se eligen "
                    "cargos públicos de elección popular federales como lo son "
                    "Presidente de la República, Diputados Federales y Senadores."
                ),
                "options": [
                    ("A", "Proceso Electoral Federal.", True),
                    ("B", "Proceso Electoral Local.", False),
                    ("C", "Proceso Electoral Concurrente.", False),
                ],
            },
            {
                "number": 10,
                "text": (
                    "De conformidad con lo establecido en la Ley General de "
                    "Instituciones y Procedimientos Electorales, ¿cómo se "
                    "denomina al conjunto de reuniones públicas, asambleas, "
                    "marchas y, en general, actos en los cuales las personas "
                    "precandidatas se dirigen a sus afiliados, simpatizantes o "
                    "al electorado para obtener su respaldo?"
                ),
                "options": [
                    ("A", "Actos de Precampaña", True),
                    ("B", "Veda electoral", False),
                    ("C", "Actos de Campaña", False),
                ],
            },
        ]

        for question_data in questions_data:

            question = Question(
                number=question_data["number"],
                text=question_data["text"],
                module_id=1,
            )

            db.add(question)
            db.flush()

            for position, (
                letter,
                option_text,
                is_correct,
            ) in enumerate(
                question_data["options"]
            ):
                db.add(
                    Option(
                        question_id=question.id,
                        letter=letter,
                        text=option_text,
                        is_correct=is_correct,
                        position=position,
                    )
                )

        db.commit()


def seed_module2_questions() -> None:
    module2_questions = [
        (
            "De conformidad con lo previsto en el artículo 14 ter del Código Penal del Estado de Tamaulipas, el delito es la conducta típica, antijurídica y culpable a la que se atribuye una o varias sanciones penales.",
            ["La culpabilidad", "El derecho penal.", "El delito"],
            "C",
        ),
        (
            "Es el acto u omisión que contraviene las disposiciones legales en materia electoral y que atenta contra la certeza y efectividad del sufragio.",
            ["Delito electoral", "Tipicidad", "Conducta"],
            "A",
        ),
        (
            "Solicitar votos por paga, promesa de dinero u otra contraprestación durante la campaña electoral, el día de la jornada electoral o en los tres días previos a esta corresponde a un delito electoral. ¿Cuál es el elemento temporal que exige esta descripción?",
            ["que exista un pago de por medio.", "que la conducta se lleve a cabo durante la campaña electoral, el día de la jornada electoral o tres días previos a la misma.", "que exista una promesa previa de pago."],
            "B",
        ),
        (
            "¿Cuáles de los siguientes delitos electorales admiten prisión preventiva oficiosa?",
            ["traslado/acarreo de votantes.", "uso de programas sociales con fines electorales.", "compra de votos."],
            "B",
        ),
        (
            "¿Qué autoridad electoral en materia penal será competente para conocer de un delito electoral cuando existan indicios suficientes de financiamiento indebido de una campaña electoral proveniente de la delincuencia organizada?",
            ["Fiscalía Especializada en Materia de Delitos Electorales (FISEL) de la FGR.", "Fiscalía Especializada en Delitos Electorales de Tamaulipas (FEDE) de la FGJ.", "Unidad Técnica de Fiscalización del INE."],
            "A",
        ),
        (
            "¿Cuál es la autoridad electoral competente para conocer de un delito electoral surgido en una elección de alcaldías y diputaciones locales, como el uso de vehículos del ayuntamiento para asistir a actos de campaña?",
            ["Fiscalía Especializada en Materia de Delitos Electorales (FISEL) de la FGR", "Fiscalía Especializada en Delitos Electorales de Tamaulipas (FEDE)", "Tribunal Electoral del Poder Judicial de la Federación."],
            "B",
        ),
        (
            "¿Cuál es la característica del voto que se transgrede cuando una persona pretende votar con una credencial que no le pertenece?",
            ["intransferible", "secreto", "libre"],
            "A",
        ),
        (
            "¿Cuál es el principio constitucional que se transgrede cuando se alteran los resultados electorales o se introducen boletas previamente marcadas en favor de algún partido político o candidato?",
            ["oralidad y publicidad.", "lealtad, objetividad y buena fe.", "elecciones libres, auténticas y periódicas"],
            "C",
        ),
        (
            "¿Cuál es el principio que garantiza condiciones de igualdad real y justicia para todos los partidos políticos y candidatos? Este principio busca que ningún participante tenga ventajas indebidas que afecten los resultados de la elección y se transgrede cuando se destinan bienes o servicios públicos en beneficio de un candidato o partido político.",
            ["equidad en la contienda", "máxima publicidad", "oralidad"],
            "A",
        ),
        (
            "¿De cuántos artículos se compone la Ley General en Materia de Delitos Electorales?",
            ["30", "70", "26"],
            "C",
        ),
        (
            "¿Quiénes tienen prohibido asistir a eventos partidistas con uniforme oficial institucional o en vehículos oficiales?",
            [
                "Servidores públicos.",
                "Candidatos.",
                "Representantes de Partido Político.",
            ],
            "A",
        ),
        (
            "¿Cuáles son las características de los delitos electorales?",
            [
                "Graves, de querella, culposos.",
                "Administrativos, sancionadores",
                "De oficio, no graves, dolosos.",
            ],
            "C",
        ),
        (
            "¿En qué Ley se encuentran previstos los delitos electorales?",
            [
                "Código Penal del Estado de Tamaulipas.",
                "Ley General en Materia de Delitos Electorales",
                "Ley General de Instituciones y Procedimientos Electorales",
            ],
            "B",
        ),
        (
            "En el procedimiento administrativo sancionador pueden ser sancionados los partidos políticos, precandidatos y candidatos, candidaturas independientes, personas físicas y morales, personas extranjeras y concesionarios de radio y televisión (artículo 422 de la LGIPE).",
            ["Verdadero", "Falso"],
            "A",
        ),
        (
            "¿Cuáles son las consecuencias que tiene la comisión de un delito electoral?",
            [
                "amonestación, disculpas públicas, multa, retiro de candidaturas.",
                "pena de prisión / suspensión o inhabilitación para ocupar cargos públicos.",
                "pena de muerte.",
            ],
            "B",
        ),
        (
            "¿Cuáles son las consecuencias que tiene la comisión de una falta administrativa en materia electoral?",
            [
                "Prisión de 2 a 6 años, suspensión de derechos políticos.",
                "Prisión preventiva, destitución definitiva de cargos públicos.",
                "amonestación, disculpas públicas, multa, retiro de candidaturas.",
            ],
            "C",
        ),
        (
            "¿Ante qué autoridad se denuncian los delitos electorales en Tamaulipas?",
            [
                "Instituto Electoral de Tamaulipas.",
                "Tribunal Electoral del Estado de Tamaulipas",
                "Fiscalía Especializada en Delitos Electorales de Tamaulipas.",
            ],
            "C",
        ),
        (
            "Los delitos electorales federales y locales se encuentran contenidos en la misma Ley General en Materia de Delitos Electorales.",
            ["Verdadero", "Falso"],
            "A",
        ),
        (
            "¿Cuál es la autoridad electoral competente para conocer de un delito electoral que surge en el contexto de una elección de Senadores y Diputados Federales?",
            [
                "Fiscalía Especializada en Materia de Delitos Electorales (FISEL) de la FGR",
                "Fiscalía Especializada en Delitos Electorales de Tamaulipas (FEDE)",
                "Tribunal Electoral del Poder Judicial de la Federación.",
            ],
            "A",
        ),
        (
            "¿Cuál es la característica del voto que se transgrede cuando una persona solicita evidencia del sentido del voto, como podría ser mostrar una fotografía de la boleta marcada?",
            ["intransferible", "secreto", "universal"],
            "B",
        ),
        (
            "¿Cuál es la característica del voto que se transgrede cuando una persona servidora pública obliga, presiona o amenaza a sus subordinados para que voten por un candidato o partido político en particular?",
            ["universal", "libre", "secreto"],
            "B",
        ),
        (
            "De acuerdo con la redacción vigente del artículo 7, fracción VII, de la Ley General en Materia de Delitos Electorales, solamente se puede sancionar penalmente a quien solicita votos a cambio de dinero, pero no al ciudadano que vende su voto.",
            ["Verdadero.", "Falso"],
            "A",
        ),
    ]

    with SessionLocal() as db:
        existing = db.scalar(
            select(Question.id)
            .where(Question.module_id == 2)
            .limit(1)
        )
        if existing:
            return

        for number, (text, option_texts, correct_letter) in enumerate(module2_questions, start=1):
            question = Question(
                number=number,
                module_id=2,
                text=text,
            )
            db.add(question)
            db.flush()

            for position, option_text in enumerate(option_texts):
                letter = chr(ord("A") + position)
                db.add(Option(
                    question_id=question.id,
                    letter=letter,
                    text=option_text,
                    is_correct=(letter == correct_letter),
                    position=position,
                ))

        db.commit()


def seed_module3_questions() -> None:
    module3_questions = [
        ("De conformidad con lo establecido en el artículo 211 del Código Nacional de Procedimientos Penales, ¿de cuántas etapas se compone el procedimiento penal acusatorio?",
         ["Averiguación previa, instrucción y juicio.", "Inicial, intermedia y Juicio.", "Demanda, emplazamiento y audiencia constitucional."], "B"),
        ("¿Cómo inicia formalmente la etapa de investigación inicial?",
         ["Inicia con la presentación de la denuncia, querella o un requisito equivalente, o bien mediante el conocimiento directo que la autoridad (policía) tenga de un hecho con apariencia de delito.", "Inicia con la presentación de un escrito de acusación que realiza un Ministerio Público ante un Juez de Control, en el que debe especificar un hecho delictivo y las pruebas que pretende desahogar.", "Inicia con la presentación de los alegatos de apertura, para anticiparle al Tribunal de Enjuiciamiento lo que se desahogará en el Juicio."], "A"),
        ("De conformidad con lo previsto en el numeral 213 del Código Nacional de Procedimientos Penales, tiene por objeto que el Ministerio Público reúna indicios para el esclarecimiento de los hechos y, en su caso, los datos de prueba para sustentar el ejercicio de la acción penal, la acusación contra el imputado y la reparación del daño.",
         ["La investigación", "La acusación", "La sentencia"], "A"),
        ("Son aquellos delitos que la autoridad investigadora (el Ministerio Público), debe investigar por mandato de ley cuando se entera de los hechos, sin que la víctima o testigos tengan que presentar una querella formal.",
         ["Delitos de oficio.", "Delitos de querella.", "Delitos preterintencionales"], "A"),
        ("¿Cuál es la forma de persecución de los delitos electorales?",
         ["De oficio.", "De querella.", "A petición de parte."], "A"),
        ("Es una figura jurídica que se refiere al momento en que una persona es sorprendida y detenida mientras comete un delito, o inmediatamente después de haberlo hecho, por lo tanto, se permite la detención del sospechoso sin necesidad de una orden judicial previa.",
         ["Flagrancia", "Orden de comparecencia", "Orden de aprehensión"], "A"),
        ("Es un documento oficial que los policías y elementos de seguridad usan en México para registrar cualquier intervención, detención o hallazgo relacionado con un delito. ",
         ["Averiguación previa.", "Informe policial homologado (IPH).", "Boleta de infracción."], "B"),
        ("De conformidad con lo previsto en la fracción segunda inciso b) del artículo 146 del Código Nacional de Procedimientos Penales, es la detención de una persona sin orden judicial realizada inmediatamente después de cometer un delito, cuando la persona detenida es señalada por la víctima u ofendido, un testigo presencial o quien hubiere intervenido con ella en la comisión del delito.",
         ["Flagrancia por señalamiento.", "Flagrancia por hallazgo de indicios o instrumentos del delito.", "Flagrancia por monitoreo de cámaras."], "A"),
        ("De acuerdo con el artículo 21 de la Constitución Política de los Estados Unidos Mexicanos, ¿qué autoridad investiga los delitos y persigue a las personas responsables en nombre de la sociedad? La Guardia Nacional y las policías actúan bajo su conducción y mando en el ejercicio de esta función.",
         ["Policía Ministerial", "Ministerio Público", "Oficial Ministerial"], "B"),
        ("¿Ante qué autoridad se denuncian los delitos electorales en Tamaulipas, en el contexto de una elección local?",
         ["Instituto Electoral de Tamaulipas.", "Tribunal Electoral del Estado de Tamaulipas.", "Fiscalía Especializada en Delitos Electorales de Tamaulipas."], "C"),
    ]

    with SessionLocal() as db:
        existing = db.scalar(
            select(Question.id)
            .where(Question.module_id == 3)
            .limit(1)
        )
        if existing:
            return

        for number, (text, option_texts, correct_letter) in enumerate(module3_questions, start=1):
            question = Question(
                number=number,
                module_id=3,
                text=text,
            )
            db.add(question)
            db.flush()

            for position, option_text in enumerate(option_texts):
                letter = chr(ord("A") + position)
                db.add(Option(
                    question_id=question.id,
                    letter=letter,
                    text=option_text,
                    is_correct=(letter == correct_letter),
                    position=position,
                ))

        db.commit()


QUESTION_TEXT_CORRECTIONS: dict[tuple[int, int], tuple[str, str]] = {
    (1, 1): (
        "¿Cuál es la característica del voto que implica que todo ciudadano debe votar de acuerdo con su preferencia política, o en favor del candidato, candidata o partido político que elija sin coacción o presión de ningún tipo.",
        "¿Cuál es la característica del voto que implica que todo ciudadano debe votar de acuerdo con su preferencia política, o en favor del candidato, candidata o partido político que elija sin coacción o presión de ningún tipo?",
    ),
    (1, 5): (
        "Cual de los siguientes cargos de elección popular no corresponde a un Proceso Electoral Local.",
        "¿Cuál de los siguientes cargos de elección popular no corresponde a un proceso electoral local?",
    ),
    (1, 6): (
        "A que mecanismo de protección de la democracia pertenecen las Fiscalías Especializadas en Delitos Electorales.",
        "¿A qué mecanismo de protección de la democracia pertenecen las Fiscalías Especializadas en Delitos Electorales?",
    ),
    (1, 10): (
        "De conformidad a lo establecido en la Ley General de Instituciones y Procedimientos Electorales, se entiende como el conjunto de reuniones públicas, asambleas, marchas y en general aquellos actos en los cuales los precandidatos a una candidatura se dirigen a los afiliados, simpatizantes o al electorado en general, con el objetivo de obtener su respaldo para ser postulado como candidato a un cargo de elección popular.",
        "De conformidad con lo establecido en la Ley General de Instituciones y Procedimientos Electorales, ¿cómo se denomina al conjunto de reuniones públicas, asambleas, marchas y, en general, actos en los cuales las personas precandidatas se dirigen a sus afiliados, simpatizantes o al electorado para obtener su respaldo?",
    ),
    (2, 1): (
        "De conformidad con lo previsto en el Artículo 14 ter del Código Penal del Estado de Tamaulipas, es entendido como la conducta típica, antijuridica y culpable a la que se le atribuyen una o varias sanciones penales.",
        "De conformidad con lo previsto en el artículo 14 ter del Código Penal del Estado de Tamaulipas, el delito es la conducta típica, antijurídica y culpable a la que se atribuye una o varias sanciones penales.",
    ),
    (2, 3): (
        "Solicitar votos por paga, promesa de dinero u otra contraprestación, durante la campaña electoral, el día de la jornada electoral o en los tres días previos a la misma, corresponde a un delito electoral ¿cuál es el elemento temporal que exige esta descripción?",
        "Solicitar votos por paga, promesa de dinero u otra contraprestación durante la campaña electoral, el día de la jornada electoral o en los tres días previos a esta corresponde a un delito electoral. ¿Cuál es el elemento temporal que exige esta descripción?",
    ),
    (2, 4): (
        "De los siguientes delitos electorales ¿cuáles admiten prisión preventiva oficiosa?",
        "¿Cuáles de los siguientes delitos electorales admiten prisión preventiva oficiosa?",
    ),
    (2, 5): (
        "Que autoridad electoral en material penal será competente para conocer de un delito electoral, cuando existen indicios suficientes para establecer el financiamiento indebido de alguna campaña electoral proveniente de la Delincuencia Organizada.",
        "¿Qué autoridad electoral en materia penal será competente para conocer de un delito electoral cuando existan indicios suficientes de financiamiento indebido de una campaña electoral proveniente de la delincuencia organizada?",
    ),
    (2, 6): (
        "¿Cuál es la autoridad electoral que será competente de conocer de un delito electoral que surge en el contexto de una elección de Alcaldías y Diputaciones locales, como pudiera ser la utilización de vehículos del ayuntamiento para asistir a actos de campaña?",
        "¿Cuál es la autoridad electoral competente para conocer de un delito electoral surgido en una elección de alcaldías y diputaciones locales, como el uso de vehículos del ayuntamiento para asistir a actos de campaña?",
    ),
    (2, 7): (
        "¿Cuál es la característica del voto que se trasgrede cuando una persona pretende votar con una credencial que no le pertenece?",
        "¿Cuál es la característica del voto que se transgrede cuando una persona pretende votar con una credencial que no le pertenece?",
    ),
    (2, 8): (
        "¿Cuál es la principio constitucional que se trasgrede cuando se alteran los resultados electorales, o se introducen boletas previamente marcadas en favor de algún partido político o candidato.",
        "¿Cuál es el principio constitucional que se transgrede cuando se alteran los resultados electorales o se introducen boletas previamente marcadas en favor de algún partido político o candidato?",
    ),
    (2, 9): (
        "¿Cuál es el principio que garantiza condiciones de igualdad real y justicia para todos los partidos políticos y candidatos? Este principio busca que ningún participante tenga ventajas indebidas que afecten los resultados de la elección y se trasgrede cuando se destinan bienes o servicios públicos en beneficio de un candidato o partido politico.",
        "¿Cuál es el principio que garantiza condiciones de igualdad real y justicia para todos los partidos políticos y candidatos? Este principio busca que ningún participante tenga ventajas indebidas que afecten los resultados de la elección y se transgrede cuando se destinan bienes o servicios públicos en beneficio de un candidato o partido político.",
    ),
    (2, 10): (
        "¿De cuantos artículos se compone la Ley General en Materia de Delitos Electorales?",
        "¿De cuántos artículos se compone la Ley General en Materia de Delitos Electorales?",
    ),
    (2, 11): (
        "¿Quienes tienen prohibido asistir a eventos partidistas con uniforme oficial institucional o en vehículos oficiales?",
        "¿Quiénes tienen prohibido asistir a eventos partidistas con uniforme oficial institucional o en vehículos oficiales?",
    ),
    (2, 14): (
        "En el procedimiento Administrativo Sancionador, pueden ser sancionados los Partidos Políticos, Precandidatos o Candidatos, candidatos independientes, personas físicas y morales, extranjeros, concesionarios de radio y televisión. (ART. 422 LGIPE)",
        "En el procedimiento administrativo sancionador pueden ser sancionados los partidos políticos, precandidatos y candidatos, candidaturas independientes, personas físicas y morales, personas extranjeras y concesionarios de radio y televisión (artículo 422 de la LGIPE).",
    ),
    (2, 17): (
        "¿Ante que autoridad se denuncian los delitos electorales en Tamaulipas?",
        "¿Ante qué autoridad se denuncian los delitos electorales en Tamaulipas?",
    ),
    (2, 20): (
        "¿Cuál es la característica del voto que se trasgrede cuando una persona solicita evidencia del sentido del voto, como pudiera ser es el mostrar fotografía de la boleta marcada?",
        "¿Cuál es la característica del voto que se transgrede cuando una persona solicita evidencia del sentido del voto, como podría ser mostrar una fotografía de la boleta marcada?",
    ),
    (2, 21): (
        "¿Cuál es la característica del voto que se trasgrede cuando un servidor público obliga, presiona o amenaza a sus subordinados a que voten por un candidato o partido político en particular?",
        "¿Cuál es la característica del voto que se transgrede cuando una persona servidora pública obliga, presiona o amenaza a sus subordinados para que voten por un candidato o partido político en particular?",
    ),
    (2, 22): (
        "De acuerdo con la redacción vigente del Artículo 7 fracción VII de la Ley General en Materia de Delitos Electorales, solamente se puede sancionar penalmente a quién solicita votos por paga (comprar), pero no al ciudadano que vende su voto (vender).",
        "De acuerdo con la redacción vigente del artículo 7, fracción VII, de la Ley General en Materia de Delitos Electorales, solamente se puede sancionar penalmente a quien solicita votos a cambio de dinero, pero no al ciudadano que vende su voto.",
    ),
    (3, 1): (
        "De conformidad a lo establecido en el Artículo 211 del Código Nacional de Procedimientos Penales, ¿de cuantas etapas se compone el Procedimiento Penal Acusatorio?",
        "De conformidad con lo establecido en el artículo 211 del Código Nacional de Procedimientos Penales, ¿de cuántas etapas se compone el procedimiento penal acusatorio?",
    ),
    (3, 10): (
        "¿Ante que autoridad se denuncian los delitos electorales en Tamaulipas, en el contexto de una elección local?",
        "¿Ante qué autoridad se denuncian los delitos electorales en Tamaulipas, en el contexto de una elección local?",
    ),
}

OPTION_TEXT_CORRECTIONS: dict[tuple[int, int, str], tuple[str, str]] = {
    (2, 5, "B"): (
        "Fiscalía Especializa en Delitos Electorales de Tamaulipas (FEDE) de la FGJ.",
        "Fiscalía Especializada en Delitos Electorales de Tamaulipas (FEDE) de la FGJ.",
    ),
}


def correct_seeded_question_texts() -> None:
    with SessionLocal() as db:
        changed = False
        for (module_id, number), (legacy_text, corrected_text) in QUESTION_TEXT_CORRECTIONS.items():
            question = db.scalar(
                select(Question).where(
                    Question.module_id == module_id,
                    Question.number == number,
                )
            )
            if question is not None and question.text == legacy_text:
                question.text = corrected_text
                changed = True
        for (module_id, question_number, letter), (legacy_text, corrected_text) in OPTION_TEXT_CORRECTIONS.items():
            option = db.scalar(
                select(Option)
                .join(Question, Question.id == Option.question_id)
                .where(
                    Question.module_id == module_id,
                    Question.number == question_number,
                    Option.letter == letter,
                )
            )
            if option is not None and option.text == legacy_text:
                option.text = corrected_text
                changed = True
        if changed:
            db.commit()


# ============================================================
# MIGRACIONES LIGERAS
# ============================================================

def ensure_user_profile_columns() -> None:
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    with engine.begin() as connection:

        if "token_version" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN token_version
                    INT NOT NULL DEFAULT 0
                    """
                )
            )

        if "municipality_other_state" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN municipality_other_state
                    VARCHAR(150) NULL
                    """
                )
            )

        if "gender_other" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN gender_other
                    VARCHAR(100) NULL
                    """
                )
            )

        if "occupation_other" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN occupation_other
                    VARCHAR(150) NULL
                    """
                )
            )


def ensure_user_foreign_keys() -> None:
    """
    Se conserva como punto de extensión para instalaciones
    existentes.

    SQLAlchemy create_all() crea las FK en instalaciones nuevas.
    """

    return


def ensure_evaluation_columns() -> None:
    inspector = inspect(engine)

    if "evaluations" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns(
            "evaluations"
        )
    }

    with engine.begin() as connection:

        if "active_attempt_key" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN active_attempt_key VARCHAR(64) NULL
                    """
                )
            )

        constraints = inspect(engine).get_unique_constraints("evaluations")
        if not any(
            set(constraint.get("column_names") or []) == {"active_attempt_key"}
            for constraint in constraints
        ):
            try:
                connection.execute(
                    text(
                        "ALTER TABLE evaluations "
                        "ADD CONSTRAINT uq_evaluation_active_attempt "
                        "UNIQUE (active_attempt_key)"
                    )
                )
            except Exception as exc:
                print(
                    "No se pudo crear la restricción única "
                    "de evaluaciones activas:",
                    exc,
                )

        if "video_session_nonce" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN video_session_nonce VARCHAR(64) NULL
                    """
                )
            )

        if "video_started_at" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN video_started_at DATETIME NULL
                    """
                )
            )

        if "current_question" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN current_question
                    INT NOT NULL DEFAULT 0
                    """
                )
            )

        if "module_id" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN module_id
                    INT NOT NULL DEFAULT 1
                    """
                )
            )

        if "attempt_number" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN attempt_number
                    INT NOT NULL DEFAULT 1
                    """
                )
            )

        if "question_order" not in columns:
            connection.execute(
                text(
                    """
                    ALTER TABLE evaluations
                    ADD COLUMN question_order TEXT NULL
                    """
                )
            )


def get_evaluation_question_order(
    db: Session,
    evaluation: Evaluation,
) -> list[int]:
    question_ids = db.scalars(
        select(Question.id)
        .where(Question.module_id == evaluation.module_id)
        .order_by(Question.number)
    ).all()

    try:
        order = json.loads(evaluation.question_order or "[]")
    except (json.JSONDecodeError, TypeError):
        order = []

    if not isinstance(order, list):
        order = []

    has_saved_order = bool(evaluation.question_order)
    valid_question_ids = set(question_ids)
    order = list(dict.fromkeys(
        question_id
        for question_id in order
        if type(question_id) is int
        and question_id in valid_question_ids
    ))

    if not has_saved_order:
        answered_ids = set(db.scalars(
            select(Answer.question_id)
            .where(Answer.evaluation_id == evaluation.id)
        ).all())
        order = [
            question_id
            for question_id in question_ids
            if question_id in answered_ids
        ]

    if len(order) > QUESTIONS_PER_EXAM:
        answered_ids = set(db.scalars(
            select(Answer.question_id)
            .where(Answer.evaluation_id == evaluation.id)
        ).all())
        previously_answered = [
            question_id
            for question_id in order
            if question_id in answered_ids
        ]
        if len(previously_answered) > QUESTIONS_PER_EXAM:
            order = SystemRandom().sample(
                previously_answered,
                QUESTIONS_PER_EXAM,
            )
        else:
            remaining_ids = [
                question_id
                for question_id in question_ids
                if question_id not in previously_answered
            ]
            order = previously_answered + SystemRandom().sample(
                remaining_ids,
                min(
                    QUESTIONS_PER_EXAM - len(previously_answered),
                    len(remaining_ids),
                ),
            )
    missing_ids = [
        question_id
        for question_id in question_ids
        if question_id not in order
    ]
    SystemRandom().shuffle(missing_ids)
    order.extend(missing_ids[:max(QUESTIONS_PER_EXAM - len(order), 0)])

    evaluation.question_order = json.dumps(order)
    evaluation.total_questions = len(order)
    db.flush()
    return order


def get_next_unanswered_index(
    db: Session,
    evaluation: Evaluation,
    question_order: list[int],
) -> int:
    answered_ids = set(db.scalars(
        select(Answer.question_id)
        .where(Answer.evaluation_id == evaluation.id)
    ).all())

    for index, question_id in enumerate(question_order):
        if question_id not in answered_ids:
            return index

    return max(len(question_order) - 1, 0)


def ensure_answer_unique_constraint() -> None:
    inspector = inspect(engine)

    if "answers" not in inspector.get_table_names():
        return

    constraints = inspector.get_unique_constraints(
        "answers"
    )

    for constraint in constraints:

        columns = constraint.get(
            "column_names"
        ) or []

        if set(columns) == {
            "evaluation_id",
            "question_id",
        }:
            return

    with engine.begin() as connection:

        try:

            connection.execute(
                text(
                    """
                    ALTER TABLE answers
                    ADD CONSTRAINT
                    uq_answer_evaluation_question
                    UNIQUE (
                        evaluation_id,
                        question_id
                    )
                    """
                )
            )

            print(
                "Restricción única de answers creada."
            )

        except Exception as exc:

            print(
                "No se pudo crear la restricción "
                "única de answers:",
                exc,
            )


def ensure_question_module_column() -> None:
    inspector = inspect(engine)
    if "questions" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("questions")
    }
    with engine.begin() as connection:
        if "module_id" not in columns:
            connection.execute(text(
                "ALTER TABLE questions "
                "ADD COLUMN module_id INT NOT NULL DEFAULT 1"
            ))

        unique_constraints = inspector.get_unique_constraints("questions")
        for constraint in unique_constraints:
            constraint_columns = constraint.get("column_names") or []
            if constraint_columns == ["number"]:
                connection.execute(text(
                    f"ALTER TABLE questions DROP INDEX `{constraint['name']}`"
                ))

        current_constraints = inspect(engine).get_unique_constraints("questions")
        if not any(
            set(constraint.get("column_names") or []) == {"module_id", "number"}
            for constraint in current_constraints
        ):
            try:
                connection.execute(text(
                    "ALTER TABLE questions ADD CONSTRAINT "
                    "uq_question_module_number UNIQUE (module_id, number)"
                ))
            except Exception as exc:
                print("No se pudo crear la restricción de módulos de questions:", exc)


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_database() -> None:

    ensure_database_exists()

    wait_for_database()

    Base.metadata.create_all(
        bind=engine
    )

    ensure_user_profile_columns()

    ensure_user_foreign_keys()

    ensure_evaluation_columns()

    ensure_answer_unique_constraint()

    ensure_question_module_column()

    seed_profile_catalogs()

    seed_questions()

    seed_module2_questions()

    seed_module3_questions()

    correct_seeded_question_texts()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Evaluación FEDE - FGJ Tamaulipas",
    version="3.0.0",
)


# ============================================================
# CORS
# ============================================================

cors_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5174",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in cors_origins_raw.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# VALIDATION ERRORS
# ============================================================

@app.exception_handler(
    RequestValidationError
)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    labels = {
        "email": "correo electrónico",
        "password": "contraseña",
        "new_password": "nueva contraseña",
        "token": "enlace de recuperación",
        "curp": "CURP",
        "first_name": "nombre",
        "paternal_surname": "apellido paterno",
        "maternal_surname": "apellido materno",
        "question_id": "pregunta",
        "option_id": "respuesta",
        "module_id": "módulo",
    }
    messages = []
    for error in exc.errors():
        field = labels.get(str(error.get("loc", ["dato"])[-1]), "dato")
        kind = error.get("type", "")
        if kind in {"missing", "value_error.missing"}:
            messages.append(f"El campo {field} es obligatorio.")
        elif kind == "value_error.email":
            messages.append("Ingresa un correo electrónico válido.")
        elif kind in {"string_too_short", "string_too_long", "greater_than_equal", "less_than_equal"}:
            messages.append(f"Revisa la longitud o el valor del campo {field}.")
        else:
            messages.append(f"El campo {field} tiene un formato o valor no válido.")
    return JSONResponse(
        status_code=422,
        content={"detail": " ".join(dict.fromkeys(messages)) or "Revisa los datos enviados e inténtalo de nuevo."},
    )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():
    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY debe configurarse con al menos 32 caracteres aleatorios."
        )
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
# AUTH
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


AUTH_FAILURE_LIMIT = 5
AUTH_FAILURE_WINDOW_MINUTES = 15


def auth_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host[:255]
    return "unknown"


def _security_state(
    db: Session,
    scope: str,
    identifier: str,
):
    return db.scalar(
        select(AuthSecurityState).where(
            AuthSecurityState.scope == scope,
            AuthSecurityState.identifier == identifier,
        )
    )


def check_auth_security(db: Session, scope: str, identifier: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    state = _security_state(db, scope, identifier)
    if not state:
        return

    window_expires = state.window_started_at + timedelta(
        minutes=AUTH_FAILURE_WINDOW_MINUTES
    )
    if window_expires <= now:
        db.delete(state)
        db.commit()
        return

    if state.failed_attempts >= AUTH_FAILURE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Espera 15 minutos antes de volver a intentarlo.",
        )


def record_auth_failure(db: Session, scope: str, identifier: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    state = _security_state(db, scope, identifier)
    if not state:
        state = AuthSecurityState(
            scope=scope,
            identifier=identifier[:255],
            failed_attempts=1,
            window_started_at=now,
        )
        db.add(state)
    else:
        if state.window_started_at + timedelta(
            minutes=AUTH_FAILURE_WINDOW_MINUTES
        ) <= now:
            state.failed_attempts = 1
            state.window_started_at = now
        else:
            state.failed_attempts += 1
    db.commit()


def clear_auth_failures(db: Session, scope: str, identifier: str) -> None:
    state = _security_state(db, scope, identifier)
    if state:
        db.delete(state)
        db.commit()


def create_access_token(
    user: User,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "tv": user.token_version,
        "jti": uuid4().hex,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    if not token:
        raise HTTPException(
            status_code=401,
            detail="No autenticado.",
        )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")
        token_version = payload.get("tv")

        if not subject:
            raise HTTPException(
                status_code=401,
                detail="Token inválido.",
            )

        if not isinstance(token_version, int):
            raise HTTPException(
                status_code=401,
                detail="Token inválido.",
            )

        user_id = int(subject)

    except (
        JWTError,
        ValueError,
        TypeError,
    ):

        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado.",
        )

    user = db.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado.",
        )

    if token_version != user.token_version:
        raise HTTPException(
            status_code=401,
            detail="Sesión revocada.",
        )

    return user


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class CatalogItemOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class StateOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class MunicipalityOut(BaseModel):
    id: int
    state_id: int
    name: str
    code: str | None = None
    is_other: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class RegisterIn(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[^\x00-\x1F\x7F]+$",
    )

    paternal_surname: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[^\x00-\x1F\x7F]+$",
    )

    maternal_surname: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[^\x00-\x1F\x7F]+$",
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=255,
    )

    curp: str = Field(
        min_length=18,
        max_length=18,
        pattern=r"^[A-Z0-9]{18}$",
    )

    state_id: int = Field(ge=1)

    municipality_id: int = Field(ge=1)

    municipality_other: str | None = Field(default=None, max_length=150)

    municipality_other_state: str | None = Field(default=None, max_length=150)

    gender_id: int | None = Field(default=None, ge=1)

    gender_other: str | None = Field(default=None, max_length=100)

    age_range_id: int | None = Field(default=None, ge=1)

    occupation_id: int | None = Field(default=None, ge=1)

    occupation_other: str | None = Field(default=None, max_length=150)

    sector_id: int | None = Field(default=None, ge=1)

    indigenous_id: int | None = Field(default=None, ge=1)

    afro_mexican_id: int | None = Field(default=None, ge=1)

    disability_id: int | None = Field(default=None, ge=1)

    lgbtttiq_id: int | None = Field(default=None, ge=1)

    education_level_id: int | None = Field(default=None, ge=1)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=32, max_length=200)
    new_password: str = Field(min_length=8, max_length=255)


class UserOut(BaseModel):
    id: int
    first_name: str
    paternal_surname: str
    maternal_surname: str
    email: str
    curp: str

    municipality: MunicipalityOut | None = None

    municipality_other: str | None = None

    municipality_other_state: str | None = None

    gender: CatalogItemOut | None = None

    gender_other: str | None = None

    age_range: CatalogItemOut | None = None

    occupation: CatalogItemOut | None = None

    occupation_other: str | None = None

    sector: CatalogItemOut | None = None

    indigenous_id: int | None = None
    afro_mexican_id: int | None = None
    disability_id: int | None = None
    lgbtttiq_id: int | None = None

    education_level: CatalogItemOut | None = None

    full_name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SaveAnswerIn(BaseModel):
    question_id: int
    option_id: int


class AnswerIn(BaseModel):
    question_id: int
    option_id: int


class FinishIn(BaseModel):
    answers: list[AnswerIn] = Field(
        default_factory=list
    )


class ProgressIn(BaseModel):
    current_question: int = Field(
        ge=0
    )


class VideoCompletedIn(BaseModel):
    nonce: str = Field(min_length=32, max_length=64)
    played_seconds: float = Field(ge=10)


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "evaluacion-fede",
    }


# ============================================================
# CATALOGS
# ============================================================

@app.get(
    "/api/catalogs/states",
    response_model=list[StateOut],
)
def get_states(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(State)
        .order_by(State.name)
    ).all()


@app.get(
    "/api/catalogs/municipalities",
    response_model=list[MunicipalityOut],
)
def get_municipalities(
    state_id: int | None = None,
    db: Session = Depends(get_db),
):

    query = select(
        Municipality
    )

    if state_id is not None:
        query = query.where(
            Municipality.state_id ==
            state_id
        )

    query = query.order_by(
        Municipality.name
    )

    return db.scalars(query).all()


@app.get(
    "/api/catalogs/genders",
    response_model=list[CatalogItemOut],
)
def get_genders(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Gender)
        .order_by(Gender.id)
    ).all()


@app.get(
    "/api/catalogs/age-ranges",
    response_model=list[CatalogItemOut],
)
def get_age_ranges(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(AgeRange)
        .order_by(AgeRange.id)
    ).all()


@app.get(
    "/api/catalogs/occupations",
    response_model=list[CatalogItemOut],
)
def get_occupations(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Occupation)
        .order_by(Occupation.name)
    ).all()


@app.get(
    "/api/catalogs/sectors",
    response_model=list[CatalogItemOut],
)
def get_sectors(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Sector)
        .order_by(Sector.id)
    ).all()


@app.get(
    "/api/catalogs/yes-no",
    response_model=list[CatalogItemOut],
)
def get_yes_no(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(YesNoOption)
        .order_by(YesNoOption.id)
    ).all()


@app.get(
    "/api/catalogs/education-levels",
    response_model=list[CatalogItemOut],
)
def get_education_levels(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(EducationLevel)
        .order_by(EducationLevel.id)
    ).all()


# ============================================================
# AUTH REGISTER
# ============================================================

@app.post(
    "/api/auth/register",
    response_model=UserOut,
)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
):

    email = data.email.strip().lower()

    curp = data.curp.strip().upper()

    existing_email = db.scalar(
        select(User)
        .where(
            User.email == email
        )
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado.",
        )

    existing_curp = db.scalar(
        select(User)
        .where(
            User.curp == curp
        )
    )

    if existing_curp:
        raise HTTPException(
            status_code=409,
            detail="La CURP ya está registrada.",
        )

    if not db.get(State, data.state_id):
        raise HTTPException(
            status_code=400,
            detail="Estado inválido.",
        )

    municipality = db.get(
        Municipality,
        data.municipality_id,
    )

    if not municipality:
        raise HTTPException(
            status_code=400,
            detail="Municipio inválido.",
        )

    if municipality.state_id != data.state_id:
        raise HTTPException(
            status_code=400,
            detail="El municipio seleccionado no corresponde al estado.",
        )

    if data.gender_id is not None:

        if not db.get(
            Gender,
            data.gender_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Género inválido.",
            )

    if data.age_range_id is not None:

        if not db.get(
            AgeRange,
            data.age_range_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Rango de edad inválido.",
            )

    if data.occupation_id is not None:

        if not db.get(
            Occupation,
            data.occupation_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Ocupación inválida.",
            )

    if data.sector_id is not None:

        if not db.get(
            Sector,
            data.sector_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Sector inválido.",
            )

    if data.education_level_id is not None:

        if not db.get(
            EducationLevel,
            data.education_level_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Nivel educativo inválido.",
            )

    for field_name, catalog_id in (
        ("Indígena", data.indigenous_id),
        ("Afrodescendiente", data.afro_mexican_id),
        ("Discapacidad", data.disability_id),
        ("LGBTTTIQ+", data.lgbtttiq_id),
    ):
        if catalog_id is not None and not db.get(YesNoOption, catalog_id):
            raise HTTPException(
                status_code=400,
                detail=f"Valor de {field_name} inválido.",
            )

    user = User(
        first_name=data.first_name.strip(),
        paternal_surname=data.paternal_surname.strip(),
        maternal_surname=data.maternal_surname.strip(),
        email=email,
        curp=curp,
        hashed_password=hash_password(
            data.password
        ),
        municipality_id=data.municipality_id,
        municipality_other=data.municipality_other,
        municipality_other_state=data.municipality_other_state,
        gender_id=data.gender_id,
        gender_other=data.gender_other,
        age_range_id=data.age_range_id,
        occupation_id=data.occupation_id,
        occupation_other=data.occupation_other,
        sector_id=data.sector_id,
        indigenous_id=data.indigenous_id,
        afro_mexican_id=data.afro_mexican_id,
        disability_id=data.disability_id,
        lgbtttiq_id=data.lgbtttiq_id,
        education_level_id=data.education_level_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# AUTH LOGIN
# ============================================================

def send_password_reset_email(recipient: str, reset_url: str) -> bool:
    if not MAIL_HOST or not MAIL_JWT or not MAIL_FROM_ADDRESS:
        logging.error("Faltan variables de entorno para enviar correos de recuperación.")
        return False

    safe_reset_url = escape(reset_url, quote=True)
    body = {
        "from": MAIL_FROM_ADDRESS,
        "to": recipient,
        "email": recipient,
        "subject": "Recupera tu contraseña",
        "message": f"""<!doctype html>
<html lang="es">
  <body style="margin:0;padding:32px 16px;background-color:#f5f5f4;font-family:Arial,Helvetica,sans-serif;color:#292928;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;margin:0 auto;background-color:#ffffff;border:1px solid #e4e4e3;border-radius:16px;">
      <tr>
        <td style="padding:36px 32px;text-align:center;">
          <h1 style="margin:0 0 16px;font-size:24px;line-height:1.3;color:#292928;">Recupera tu contraseña</h1>
          <p style="margin:0 0 28px;font-size:15px;line-height:1.7;color:#575756;">Recibimos una solicitud para cambiar la contraseña de tu cuenta. Usa el botón para crear una nueva:</p>
          <a href="{safe_reset_url}" style="display:inline-block;padding:14px 24px;border-radius:9px;background-color:#575756;color:#ffffff;text-decoration:none;font-size:15px;font-weight:bold;">Crear nueva contraseña</a>
          <p style="margin:28px 0 8px;font-size:13px;line-height:1.6;color:#777776;">Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
          <p style="margin:0;word-break:break-all;font-size:12px;line-height:1.6;"><a href="{safe_reset_url}" style="color:#575756;">{safe_reset_url}</a></p>
          <p style="margin:28px 0 0;font-size:13px;line-height:1.7;color:#777776;">Este enlace vence en {PASSWORD_RESET_EXPIRE_MINUTES} minutos y solo se puede usar una vez. Si no solicitaste el cambio, ignora este correo.</p>
        </td>
      </tr>
    </table>
  </body>
</html>""",
    }
    request = URLRequest(
        MAIL_HOST,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {MAIL_JWT}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            if 200 <= response.status < 300:
                return True
            logging.error("El servicio de correo respondió con HTTP %s.", response.status)
    except HTTPError as exc:
        logging.error("El servicio de correo respondió con HTTP %s.", exc.code)
    except (URLError, TimeoutError, OSError):
        logging.exception("No se pudo conectar con el servicio de correo.")
    return False


@app.post("/api/auth/password/forgot")
def request_password_reset(
    data: PasswordResetRequestIn,
    request: Request,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()
    ip = auth_client_ip(request)
    check_auth_security(db, "password-reset-ip", ip)
    check_auth_security(db, "password-reset-email", email)
    record_auth_failure(db, "password-reset-ip", ip)
    record_auth_failure(db, "password-reset-email", email)
    user = db.scalar(select(User).where(User.email == email))

    if user:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at <= now))
        recent_token = db.scalar(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id)
            .order_by(PasswordResetToken.created_at.desc())
        )
        if recent_token and recent_token.created_at > now - timedelta(seconds=60):
            return {"message": "Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña."}

        raw_token = token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            created_at=now,
            expires_at=now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES),
        ))
        db.commit()

        reset_url = f"{FRONTEND_URL}/?{urlencode({'reset_token': raw_token})}"
        if not send_password_reset_email(user.email, reset_url):
            db.execute(delete(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
            db.commit()

    # Respuesta genérica para no revelar si una dirección está registrada.
    return {"message": "Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña."}


@app.post("/api/auth/password/reset")
def reset_password(
    data: PasswordResetConfirmIn,
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(data.token.encode("utf-8")).hexdigest()
    reset_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if not reset_token or reset_token.expires_at <= now:
        if reset_token:
            db.delete(reset_token)
            db.commit()
        raise HTTPException(status_code=400, detail="El enlace venció o ya fue utilizado. Solicita uno nuevo.")

    user = db.get(User, reset_token.user_id)
    if not user:
        db.delete(reset_token)
        db.commit()
        raise HTTPException(status_code=400, detail="El enlace venció o ya fue utilizado. Solicita uno nuevo.")

    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    db.commit()
    return {"message": "Tu contraseña se actualizó. Ya puedes iniciar sesión."}

@app.post(
    "/api/auth/login",
    response_model=TokenOut,
)
def login(
    data: LoginIn,
    request: Request,
    db: Session = Depends(get_db),
):

    email = data.email.strip().lower()
    ip = auth_client_ip(request)
    check_auth_security(db, "login-ip", ip)
    check_auth_security(db, "login-email", email)

    user = db.scalar(
        select(User)
        .where(
            User.email == email
        )
    )

    if not user:
        record_auth_failure(db, "login-ip", ip)
        record_auth_failure(db, "login-email", email)
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas.",
        )

    if not verify_password(
        data.password,
        user.hashed_password,
    ):
        record_auth_failure(db, "login-ip", ip)
        record_auth_failure(db, "login-email", email)
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas.",
        )

    clear_auth_failures(db, "login-ip", ip)
    clear_auth_failures(db, "login-email", email)

    token = create_access_token(
        user
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


# ============================================================
# AUTH ME
# ============================================================

@app.get(
    "/api/auth/me",
    response_model=UserOut,
)
def me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return current_user


@app.post("/api/auth/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.token_version += 1
    db.commit()
    return {"success": True}


# ============================================================
# QUESTIONS
# ============================================================

@app.get("/api/questions")
def get_questions(
    module_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    if module_id not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Módulo no válido.")

    _require_available_module(db, current_user.id, module_id)

    questions = db.scalars(
        select(Question)
        .where(Question.module_id == module_id)
        .order_by(Question.number)
    ).all()

    return [
        {
            "id": question.id,
            "number": question.number,
            "text": question.text,
            "options": [
                {
                    "id": option.id,
                    "letter": option.letter,
                    "text": option.text,
                }
                for option in question.options
            ],
        }
        for question in questions
    ]


def _module_statuses_for_user(db: Session, user_id: int) -> list[dict]:
    module_names = {
        1: "Nociones básicas de derecho electoral",
        2: "Delitos Electorales y su investigación en el Contexto de los Procesos Electorales Locales",
        3: "Integración de la carpeta de investigación, primer respondiente, retos en la investigación y cultura de prevención",
    }
    result = []

    for module_id in COURSE_MODULE_IDS:
        questions_available = int(db.scalar(
            select(text("COUNT(*)")).select_from(Question).where(
                Question.module_id == module_id
            )
        ) or 0) > 0
        completed = db.scalars(
            select(Evaluation).where(
                Evaluation.user_id == user_id,
                Evaluation.module_id == module_id,
                Evaluation.completed_at.is_not(None),
            ).order_by(Evaluation.completed_at.desc())
        ).all()
        in_progress = db.scalar(
            select(Evaluation.id).where(
                Evaluation.user_id == user_id,
                Evaluation.module_id == module_id,
                Evaluation.completed_at.is_(None),
            ).limit(1)
        ) is not None
        best_score = max(
            (
                evaluation_percentage(item)
                for item in completed
                if evaluation_percentage(item) is not None
            ),
            default=None,
        )
        passed = best_score is not None and best_score >= PASSING_SCORE
        attempts_remaining = max(0, 3 - len(completed))
        result.append({
            "module_id": module_id,
            "name": module_names[module_id],
            "attempts": len(completed),
            "attempts_remaining": attempts_remaining,
            "best_score": best_score,
            "passed": passed,
            "in_progress": in_progress,
            "questions_available": questions_available,
            "available": (
                not passed
                and all(previous["passed"] for previous in result)
                and (in_progress or attempts_remaining > 0)
            ),
        })

    return result


def _require_available_module(db: Session, user_id: int, module_id: int) -> None:
    statuses = _module_statuses_for_user(db, user_id)
    status = next(module for module in statuses if module["module_id"] == module_id)

    if status["passed"]:
        raise HTTPException(
            status_code=409,
            detail="Este módulo ya fue acreditado y no se puede repetir.",
        )

    if not all(
        module["passed"]
        for module in statuses
        if module["module_id"] < module_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Debes acreditar los módulos anteriores antes de continuar.",
        )

    if not status["in_progress"] and status["attempts_remaining"] == 0:
        raise HTTPException(
            status_code=409,
            detail="Has agotado los 3 intentos disponibles para este módulo.",
        )


@app.get("/api/modules/status")
def get_modules_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = _module_statuses_for_user(db, current_user.id)

    return {
        "modules": result,
        "course": {
            "key": COURSE_KEY,
            "name": COURSE_NAME,
            "completed": len([module for module in result if module["passed"]]) == len(COURSE_MODULE_IDS),
        },
    }


def _passing_course_evaluations(db: Session, user_id: int) -> dict[int, Evaluation]:
    evaluations = db.scalars(
        select(Evaluation)
        .where(
            Evaluation.user_id == user_id,
            Evaluation.module_id.in_(COURSE_MODULE_IDS),
            Evaluation.completed_at.is_not(None),
        )
        .order_by(Evaluation.completed_at.desc())
    ).all()
    passing: dict[int, Evaluation] = {}
    for evaluation in evaluations:
        score = evaluation_percentage(evaluation)
        if score is not None and score >= PASSING_SCORE:
            passing.setdefault(evaluation.module_id, evaluation)
    return passing


def _certificate_issue_data(certificate: Certificate) -> dict:
    return {
        "folio": certificate.folio,
        "course_key": certificate.course_key,
        "course_name": COURSE_NAME,
        "user_name": certificate.user_name,
        "issued_at": certificate.issued_at,
    }


@app.post("/api/certificates/generate")
def generate_certificate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    passing_evaluations = _passing_course_evaluations(db, current_user.id)
    if set(passing_evaluations) != set(COURSE_MODULE_IDS):
        raise HTTPException(
            status_code=409,
            detail="Debes acreditar los tres módulos para generar la constancia del curso.",
        )

    certificate = db.scalar(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.course_key == COURSE_KEY,
        )
    )
    if not certificate:
        issued_at = datetime.now(timezone.utc)
        certificate = Certificate(
            user_id=current_user.id,
            course_key=COURSE_KEY,
            folio=f"FEDE-{issued_at.year}-{uuid4().hex.upper()}",
            user_name=current_user.full_name,
            issued_at=issued_at,
        )
        db.add(certificate)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            certificate = db.scalar(
                select(Certificate).where(
                    Certificate.user_id == current_user.id,
                    Certificate.course_key == COURSE_KEY,
                )
            )
            if certificate is None:
                raise
        else:
            db.refresh(certificate)

    return _certificate_issue_data(certificate)


@app.get("/api/certificates/verify/{folio}")
def verify_certificate(
    folio: str,
    db: Session = Depends(get_db),
):
    certificate = db.scalar(
        select(Certificate).where(Certificate.folio == folio)
    )
    if not certificate and re.fullmatch(r"[A-Fa-f0-9]{32}", folio):
        certificate = db.scalar(
            select(Certificate).where(
                Certificate.folio.endswith(f"-{folio.upper()}")
            )
        )
    if not certificate or certificate.course_key != COURSE_KEY:
        return {"valid": False, "message": "La constancia no es válida."}

    user = db.get(User, certificate.user_id)
    if not user:
        return {"valid": False, "message": "La constancia no es válida."}

    return {
        "valid": True,
        "message": "La constancia es válida.",
        "folio": certificate.folio,
        "issued_at": certificate.issued_at,
        "user_name": certificate.user_name,
        "municipality": user.municipality_other or (
            user.municipality.name if user.municipality else None
        ),
        "sector": user.sector.name if user.sector else None,
        "course": {
            "key": certificate.course_key,
            "name": COURSE_NAME,
        },
    }


# ============================================================
# EVALUATIONS - CURRENT
# ============================================================

@app.get(
    "/api/evaluations/current"
)
def get_current_evaluation(
    module_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    if module_id not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Módulo no válido.")

    _require_available_module(db, current_user.id, module_id)

    evaluation = db.scalar(
        select(Evaluation)
        .where(
            Evaluation.user_id ==
            current_user.id,
            Evaluation.module_id == module_id,

            Evaluation.completed_at.is_(None),
        )
        .order_by(
            Evaluation.started_at.desc()
        )
    )

    if not evaluation:
        evaluation = db.scalar(
            select(Evaluation)
            .where(
                Evaluation.user_id == current_user.id,
                Evaluation.module_id == module_id,
                Evaluation.completed_at.is_not(None),
            )
            .order_by(Evaluation.completed_at.desc())
        )
        if not evaluation:
            return {"has_evaluation": False, "evaluation": None}
        return {
            "has_evaluation": True,
            "evaluation": {
                "id": evaluation.id,
                "completed": True,
                "video_completed": evaluation.video_completed,
                "started_at": evaluation.started_at,
                "completed_at": evaluation.completed_at,
                "current_question": evaluation.current_question,
                "question_order": [],
                "answered_count": evaluation.correct_answers,
                "total_questions": evaluation.total_questions,
                "score": evaluation_percentage(evaluation),
                "correct": evaluation.correct_answers,
                "attempt_number": evaluation.attempt_number,
                "attempts_remaining": max(0, 3 - int(db.scalar(
                    select(text("COUNT(*)")).select_from(Evaluation).where(
                        Evaluation.user_id == current_user.id,
                        Evaluation.module_id == module_id,
                        Evaluation.completed_at.is_not(None),
                    )
                ) or 0)),
                "passed": (evaluation_percentage(evaluation) or 0) >= PASSING_SCORE,
                "answers": [],
            },
        }

    had_question_order = bool(evaluation.question_order)
    question_order = get_evaluation_question_order(
        db,
        evaluation,
    )
    if not had_question_order:
        evaluation.current_question = min(
            get_next_unanswered_index(
                db,
                evaluation,
                question_order,
            ),
            max(len(question_order) - 1, 0),
        )
    evaluation.current_question = min(
        evaluation.current_question,
        max(len(question_order) - 1, 0),
    )
    db.commit()

    answers = db.scalars(
        select(Answer)
        .where(
            Answer.evaluation_id ==
            evaluation.id
        )
    ).all()

    return {
        "has_evaluation": True,
        "evaluation": {
            "id": evaluation.id,
            "completed": False,
            "video_completed":
                evaluation.video_completed,
            "started_at":
                evaluation.started_at,
            "current_question":
                evaluation.current_question,
            "question_order":
                question_order,
            "answered_count":
                len(answers),
            "total_questions":
                evaluation.total_questions,
            "answers": [
                {
                    "question_id":
                        answer.question_id,
                    "option_id":
                        answer.option_id,
                }
                for answer in answers
            ],
        },
    }


# ============================================================
# EVALUATIONS - START / RESUME
# ============================================================

@app.post(
    "/api/evaluations/start"
)
def start_evaluation(
    module_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    if module_id not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Módulo no válido.")

    _require_available_module(db, current_user.id, module_id)

    existing_evaluation = db.scalar(
        select(Evaluation)
        .where(
            Evaluation.user_id ==
            current_user.id,
            Evaluation.module_id == module_id,

            Evaluation.completed_at.is_(None),
        )
        .order_by(
            Evaluation.started_at.desc()
        )
    )

    # --------------------------------------------------------
    # RECUPERAR EVALUACIÓN EXISTENTE
    # --------------------------------------------------------

    if existing_evaluation:
        if not existing_evaluation.active_attempt_key:
            existing_evaluation.active_attempt_key = (
                f"{current_user.id}:{module_id}"
            )
        if not existing_evaluation.video_session_nonce:
            existing_evaluation.video_session_nonce = token_urlsafe(24)
            existing_evaluation.video_started_at = datetime.now(timezone.utc).replace(
                tzinfo=None
            )

        had_question_order = bool(
            existing_evaluation.question_order
        )
        question_order = get_evaluation_question_order(
            db,
            existing_evaluation,
        )
        if not had_question_order:
            existing_evaluation.current_question = min(
                get_next_unanswered_index(
                    db,
                    existing_evaluation,
                    question_order,
                ),
                max(len(question_order) - 1, 0),
            )
        existing_evaluation.current_question = min(
            existing_evaluation.current_question,
            max(len(question_order) - 1, 0),
        )
        db.commit()

        answers = db.scalars(
            select(Answer)
            .where(
                Answer.evaluation_id ==
                existing_evaluation.id
            )
        ).all()

        return {
            "evaluation_id":
                existing_evaluation.id,

            "resumed": True,

            "video_completed":
                existing_evaluation.video_completed,

            "video_session_nonce":
                existing_evaluation.video_session_nonce,

            "current_question":
                existing_evaluation.current_question,

            "question_order":
                question_order,

            "answers": [
                {
                    "question_id":
                        answer.question_id,

                    "option_id":
                        answer.option_id,
                }
                for answer in answers
            ],

            "user":
                UserOut.model_validate(
                    current_user
                ),
        }

    # --------------------------------------------------------
    # NUEVA EVALUACIÓN
    # --------------------------------------------------------

    question_pool = db.scalars(
        select(Question.id)
        .where(Question.module_id == module_id)
        .order_by(Question.number)
    ).all()
    if not question_pool:
        raise HTTPException(
            status_code=500,
            detail="No existen preguntas configuradas.",
        )
    if len(question_pool) < QUESTIONS_PER_EXAM:
        raise HTTPException(
            status_code=500,
            detail="No hay suficientes preguntas configuradas para el examen.",
        )

    completed_attempts = db.scalar(
        select(text("COUNT(*)"))
        .select_from(Evaluation)
        .where(
            Evaluation.user_id == current_user.id,
            Evaluation.module_id == module_id,
            Evaluation.completed_at.is_not(None),
        )
    )
    completed_attempts = int(completed_attempts or 0)

    previous_evaluations = db.scalars(
        select(Evaluation)
        .where(
            Evaluation.user_id == current_user.id,
            Evaluation.module_id == module_id,
            Evaluation.completed_at.is_not(None),
        )
    ).all()
    best_score = max(
        (evaluation_percentage(item) or 0 for item in previous_evaluations),
        default=None,
    )
    if best_score is not None and best_score >= PASSING_SCORE:
        raise HTTPException(
            status_code=409,
            detail="Este módulo ya fue aprobado.",
        )
    if completed_attempts >= 3:
        raise HTTPException(
            status_code=409,
            detail="Has agotado los 3 intentos disponibles para este módulo.",
        )

    question_order = SystemRandom().sample(
        question_pool,
        k=QUESTIONS_PER_EXAM,
    )

    evaluation = Evaluation(
        user_id=current_user.id,
        module_id=module_id,
        attempt_number=completed_attempts + 1,
        started_at=datetime.now(
            timezone.utc
        ),
        total_questions=len(question_order),
        video_completed=False,
        current_question=0,
        question_order=json.dumps(question_order),
        active_attempt_key=f"{current_user.id}:{module_id}",
        video_session_nonce=token_urlsafe(24),
        video_started_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    db.add(evaluation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una evaluación activa para este módulo.",
        )

    db.refresh(evaluation)

    return {
        "evaluation_id":
            evaluation.id,

        "resumed":
            False,

        "video_completed":
            False,

        "video_session_nonce":
            evaluation.video_session_nonce,

        "current_question":
            0,

        "question_order":
            question_order,

        "answers":
            [],

        "user":
            UserOut.model_validate(
                current_user
            ),
    }


# ============================================================
# EVALUATIONS - VIDEO COMPLETED
# ============================================================

@app.post(
    "/api/evaluations/{evaluation_id}/video-completed"
)
def mark_video_completed(
    evaluation_id: int,
    data: VideoCompletedIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
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

    if evaluation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a esta evaluación.",
        )

    _require_available_module(db, current_user.id, evaluation.module_id)

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    if not evaluation.video_session_nonce or not compare_digest(
        evaluation.video_session_nonce,
        data.nonce,
    ):
        raise HTTPException(
            status_code=400,
            detail="La sesión de video no es válida.",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    started_at = evaluation.video_started_at
    if not started_at:
        raise HTTPException(
            status_code=400,
            detail="La sesión de video no fue iniciada.",
        )

    elapsed_seconds = max(0.0, (now - started_at).total_seconds())
    if (
        elapsed_seconds + 1 < data.played_seconds
        or elapsed_seconds < 10
        or data.played_seconds < 10
    ):
        raise HTTPException(
            status_code=400,
            detail="Completa la reproducción antes de continuar.",
        )

    evaluation.video_completed = True

    db.commit()

    return {
        "success": True,
        "evaluation_id":
            evaluation.id,
        "video_completed":
            True,
    }


# ============================================================
# EVALUATIONS - SAVE ANSWER
# ============================================================

@app.put(
    "/api/evaluations/{evaluation_id}/answers"
)
def save_answer(
    evaluation_id: int,
    data: SaveAnswerIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # EVALUACIÓN
    # --------------------------------------------------------

    evaluation = db.get(
        Evaluation,
        evaluation_id,
    )

    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada.",
        )

    if evaluation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a esta evaluación.",
        )

    _require_available_module(db, current_user.id, evaluation.module_id)

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    if not evaluation.video_completed:
        raise HTTPException(
            status_code=400,
            detail="Debes completar el video antes de responder.",
        )

    # --------------------------------------------------------
    # PREGUNTA
    # --------------------------------------------------------

    question = db.get(
        Question,
        data.question_id,
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="La pregunta no existe.",
        )
    if question.module_id != evaluation.module_id:
        raise HTTPException(
            status_code=400,
            detail="La pregunta no pertenece a este módulo.",
        )

    # --------------------------------------------------------
    # OPCIÓN
    # --------------------------------------------------------

    option = db.get(
        Option,
        data.option_id,
    )

    if not option:
        raise HTTPException(
            status_code=400,
            detail="La opción seleccionada no existe.",
        )

    if option.question_id != question.id:
        raise HTTPException(
            status_code=400,
            detail="La opción no pertenece a la pregunta.",
        )

    question_order = get_evaluation_question_order(
        db,
        evaluation,
    )
    if question.id not in question_order:
        raise HTTPException(
            status_code=400,
            detail="La pregunta no forma parte de esta evaluación.",
        )

    existing_answer = db.scalar(
        select(Answer)
        .where(
            Answer.evaluation_id == evaluation.id,
            Answer.question_id == question.id,
        )
    )

    if existing_answer:
        existing_answer.option_id = option.id
        existing_answer.is_correct = bool(option.is_correct)
        db.commit()
        return {
            "success": True,
            "evaluation_id": evaluation.id,
            "question_id": question.id,
            "option_id": option.id,
        }

    expected_index = get_next_unanswered_index(
        db,
        evaluation,
        question_order,
    )

    if (
        expected_index >= len(question_order)
        or question_order[expected_index] != question.id
    ):
        raise HTTPException(
            status_code=409,
            detail="Debes responder la siguiente pregunta pendiente.",
        )

    answer = Answer(
        evaluation_id=evaluation.id,
        question_id=question.id,
        option_id=option.id,
        is_correct=bool(option.is_correct),
    )
    db.add(answer)
    db.commit()

    db.refresh(answer)

    return {
        "success": True,

        "evaluation_id":
            evaluation.id,

        "question_id":
            question.id,

        "option_id":
            option.id,

    }


# ============================================================
# EVALUATIONS - SAVE CURRENT QUESTION
# ============================================================

@app.put(
    "/api/evaluations/{evaluation_id}/progress"
)
def save_evaluation_progress(
    evaluation_id: int,
    data: ProgressIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
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

    if evaluation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a esta evaluación.",
        )

    _require_available_module(db, current_user.id, evaluation.module_id)

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    question_order = get_evaluation_question_order(
        db,
        evaluation,
    )
    next_unanswered = get_next_unanswered_index(
        db,
        evaluation,
        question_order,
    )

    if (
        data.current_question >= len(question_order)
        or data.current_question > next_unanswered
    ):
        raise HTTPException(
            status_code=400,
            detail="No puedes avanzar más allá de las preguntas pendientes.",
        )

    evaluation.current_question = (
        data.current_question
    )

    db.commit()

    return {
        "success": True,
        "current_question":
            evaluation.current_question,
    }


# ============================================================
# EVALUATIONS - FINISH
# ============================================================

@app.post(
    "/api/evaluations/{evaluation_id}/finish"
)
def finish_evaluation(
    evaluation_id: int,
    data: FinishIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
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

    if evaluation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a esta evaluación.",
        )

    _require_available_module(db, current_user.id, evaluation.module_id)

    if not evaluation.video_completed:
        raise HTTPException(
            status_code=400,
            detail="Debes completar el video antes de finalizar.",
        )

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    # --------------------------------------------------------
    # PREGUNTAS
    # --------------------------------------------------------

    question_order = get_evaluation_question_order(db, evaluation)
    total = len(question_order)

    if total == 0:
        raise HTTPException(
            status_code=500,
            detail="No existen preguntas configuradas.",
        )

    # --------------------------------------------------------
    # RESPUESTAS GUARDADAS
    # --------------------------------------------------------

    answers = db.scalars(
        select(Answer)
        .where(
            Answer.evaluation_id ==
            evaluation.id
        )
    ).all()

    answers_by_question = {
        answer.question_id:
            answer
        for answer in answers
    }

    # --------------------------------------------------------
    # VALIDAR PREGUNTAS PENDIENTES
    # --------------------------------------------------------

    unanswered = [
        position
        for position, question_id in enumerate(question_order, start=1)
        if question_id not in answers_by_question
    ]

    if unanswered:
        raise HTTPException(
            status_code=400,
            detail=(
                "Debes responder todas las preguntas visibles. "
                "Preguntas pendientes: "
                + ", ".join(
                    map(
                        str,
                        unanswered,
                    )
                )
            ),
        )

    # --------------------------------------------------------
    # CALCULAR
    # --------------------------------------------------------

    selected_answers = [
        answers_by_question[question_id]
        for question_id in question_order
    ]
    correct = sum(answer.is_correct for answer in selected_answers)

    score = round((correct / total) * 100)

    # --------------------------------------------------------
    # GUARDAR RESULTADO
    # --------------------------------------------------------

    evaluation.correct_answers = correct

    evaluation.total_questions = total

    evaluation.score = score

    evaluation.completed_at = (
        datetime.now(timezone.utc)
    )
    evaluation.active_attempt_key = None
    evaluation.video_session_nonce = None
    evaluation.video_started_at = None

    db.commit()

    db.refresh(evaluation)

    return {
        "success": True,

        "message":
            "Evaluación registrada correctamente.",

        "evaluation_id":
            evaluation.id,

        "score":
            score,

        "correct":
            correct,

        "total":
            total,
        "module_id":
            evaluation.module_id,
        "attempt_number":
            evaluation.attempt_number,
        "passed":
            score >= PASSING_SCORE,
    }
