from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

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
    "change-this-secret-key",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "1440",
    )
)


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
            "state_id",
            "name",
            name="uq_municipality_state_name",
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
    Inserta las preguntas únicamente si la tabla está vacía.

    Si ya tienes preguntas en producción, NO las modifica.
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
                    "¿Qué se entiende por delito electoral?"
                ),
                "options": [
                    (
                        "A",
                        "Una conducta prevista por la ley que afecta "
                        "el adecuado desarrollo de los procesos electorales.",
                        True,
                    ),
                    (
                        "B",
                        "Cualquier desacuerdo entre partidos políticos.",
                        False,
                    ),
                    (
                        "C",
                        "Una infracción exclusivamente administrativa.",
                        False,
                    ),
                    (
                        "D",
                        "Una opinión emitida durante una campaña.",
                        False,
                    ),
                ],
            },
            {
                "number": 2,
                "text": (
                    "¿Qué institución organiza las elecciones "
                    "locales en Tamaulipas?"
                ),
                "options": [
                    (
                        "A",
                        "La Fiscalía General de Justicia.",
                        False,
                    ),
                    (
                        "B",
                        "El Instituto Electoral de Tamaulipas.",
                        True,
                    ),
                    (
                        "C",
                        "El Tribunal Electoral.",
                        False,
                    ),
                    (
                        "D",
                        "La Secretaría de Seguridad Pública.",
                        False,
                    ),
                ],
            },
            {
                "number": 3,
                "text": (
                    "¿Qué autoridad jurisdiccional resuelve "
                    "controversias electorales locales?"
                ),
                "options": [
                    (
                        "A",
                        "El Tribunal Electoral de Tamaulipas.",
                        True,
                    ),
                    (
                        "B",
                        "La Fiscalía Especializada.",
                        False,
                    ),
                    (
                        "C",
                        "El Congreso de la Unión.",
                        False,
                    ),
                    (
                        "D",
                        "La Secretaría de Gobernación.",
                        False,
                    ),
                ],
            },
            {
                "number": 4,
                "text": (
                    "¿Qué derecho permite a la ciudadanía "
                    "participar mediante la emisión del voto?"
                ),
                "options": [
                    (
                        "A",
                        "Derecho de petición.",
                        False,
                    ),
                    (
                        "B",
                        "Derecho de asociación.",
                        False,
                    ),
                    (
                        "C",
                        "Derecho al sufragio.",
                        True,
                    ),
                    (
                        "D",
                        "Derecho de audiencia.",
                        False,
                    ),
                ],
            },
            {
                "number": 5,
                "text": (
                    "¿Cuál es una característica del voto "
                    "en el sistema electoral mexicano?"
                ),
                "options": [
                    (
                        "A",
                        "Es público y obligatorio para todas las personas.",
                        False,
                    ),
                    (
                        "B",
                        "Es universal, libre, secreto y directo.",
                        True,
                    ),
                    (
                        "C",
                        "Es exclusivo para servidores públicos.",
                        False,
                    ),
                    (
                        "D",
                        "Es determinado por los partidos políticos.",
                        False,
                    ),
                ],
            },
            {
                "number": 6,
                "text": (
                    "¿Qué autoridad investiga los delitos "
                    "electorales de competencia federal?"
                ),
                "options": [
                    (
                        "A",
                        "La FEDE.",
                        True,
                    ),
                    (
                        "B",
                        "El INE exclusivamente.",
                        False,
                    ),
                    (
                        "C",
                        "El Congreso del Estado.",
                        False,
                    ),
                    (
                        "D",
                        "El Tribunal Electoral local.",
                        False,
                    ),
                ],
            },
            {
                "number": 7,
                "text": (
                    "¿Qué debe garantizar una investigación "
                    "de un posible delito electoral?"
                ),
                "options": [
                    (
                        "A",
                        "La imparcialidad y el respeto al debido proceso.",
                        True,
                    ),
                    (
                        "B",
                        "La preferencia por un partido político.",
                        False,
                    ),
                    (
                        "C",
                        "La publicidad de todos los datos personales.",
                        False,
                    ),
                    (
                        "D",
                        "La eliminación de la presunción de inocencia.",
                        False,
                    ),
                ],
            },
            {
                "number": 8,
                "text": (
                    "¿Qué es el proceso electoral?"
                ),
                "options": [
                    (
                        "A",
                        "El conjunto de actos realizados para "
                        "la renovación periódica de los cargos de elección popular.",
                        True,
                    ),
                    (
                        "B",
                        "Únicamente la jornada electoral.",
                        False,
                    ),
                    (
                        "C",
                        "El periodo de campañas exclusivamente.",
                        False,
                    ),
                    (
                        "D",
                        "El proceso interno de los partidos.",
                        False,
                    ),
                ],
            },
            {
                "number": 9,
                "text": (
                    "¿Qué conducta puede constituir un delito "
                    "electoral cuando se condiciona un servicio "
                    "público a cambio del voto?"
                ),
                "options": [
                    (
                        "A",
                        "Una conducta sin consecuencias jurídicas.",
                        False,
                    ),
                    (
                        "B",
                        "Una conducta que puede constituir un delito electoral.",
                        True,
                    ),
                    (
                        "C",
                        "Una actividad exclusivamente partidista.",
                        False,
                    ),
                    (
                        "D",
                        "Una actividad administrativa ordinaria.",
                        False,
                    ),
                ],
            },
            {
                "number": 10,
                "text": (
                    "¿Qué principio busca que las personas "
                    "puedan ejercer su voto sin presión o coacción?"
                ),
                "options": [
                    (
                        "A",
                        "Secreto y libertad del voto.",
                        True,
                    ),
                    (
                        "B",
                        "Publicidad del voto.",
                        False,
                    ),
                    (
                        "C",
                        "Dependencia jerárquica.",
                        False,
                    ),
                    (
                        "D",
                        "Discrecionalidad electoral.",
                        False,
                    ),
                ],
            },
        ]

        for question_data in questions_data:

            question = Question(
                number=question_data["number"],
                text=question_data["text"],
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

    seed_profile_catalogs()

    seed_questions()


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
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
        },
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


def create_access_token(
    user_id: int,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
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

        if not subject:
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
    is_other: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class RegisterIn(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    paternal_surname: str = Field(
        min_length=1,
        max_length=100,
    )

    maternal_surname: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=255,
    )

    curp: str = Field(
        min_length=18,
        max_length=18,
    )

    municipality_id: int | None = None

    municipality_other: str | None = None

    municipality_other_state: str | None = None

    gender_id: int | None = None

    gender_other: str | None = None

    age_range_id: int | None = None

    occupation_id: int | None = None

    occupation_other: str | None = None

    sector_id: int | None = None

    indigenous_id: int | None = None

    afro_mexican_id: int | None = None

    disability_id: int | None = None

    lgbtttiq_id: int | None = None

    education_level_id: int | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


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

    if data.municipality_id is not None:

        municipality = db.get(
            Municipality,
            data.municipality_id,
        )

        if not municipality:
            raise HTTPException(
                status_code=400,
                detail="Municipio inválido.",
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

@app.post(
    "/api/auth/login",
    response_model=TokenOut,
)
def login(
    data: LoginIn,
    db: Session = Depends(get_db),
):

    email = data.email.strip().lower()

    user = db.scalar(
        select(User)
        .where(
            User.email == email
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas.",
        )

    if not verify_password(
        data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas.",
        )

    token = create_access_token(
        user.id
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


# ============================================================
# QUESTIONS
# ============================================================

@app.get("/api/questions")
def get_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    questions = db.scalars(
        select(Question)
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


# ============================================================
# EVALUATIONS - CURRENT
# ============================================================

@app.get(
    "/api/evaluations/current"
)
def get_current_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    evaluation = db.scalar(
        select(Evaluation)
        .where(
            Evaluation.user_id ==
            current_user.id,

            Evaluation.completed_at.is_(None),
        )
        .order_by(
            Evaluation.started_at.desc()
        )
    )

    if not evaluation:
        return {
            "has_evaluation": False,
            "evaluation": None,
        }

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
            "video_completed":
                evaluation.video_completed,
            "started_at":
                evaluation.started_at,
            "current_question":
                evaluation.current_question,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    existing_evaluation = db.scalar(
        select(Evaluation)
        .where(
            Evaluation.user_id ==
            current_user.id,

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

            "current_question":
                existing_evaluation.current_question,

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

    total_questions = db.scalar(
        select(text("COUNT(*)"))
        .select_from(Question)
    )

    total_questions = int(
        total_questions or 0
    )

    if total_questions == 0:
        raise HTTPException(
            status_code=500,
            detail="No existen preguntas configuradas.",
        )

    evaluation = Evaluation(
        user_id=current_user.id,
        started_at=datetime.now(
            timezone.utc
        ),
        total_questions=total_questions,
        video_completed=False,
        current_question=0,
    )

    db.add(evaluation)

    db.commit()

    db.refresh(evaluation)

    return {
        "evaluation_id":
            evaluation.id,

        "resumed":
            False,

        "video_completed":
            False,

        "current_question":
            0,

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

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
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

    # --------------------------------------------------------
    # RESPUESTA EXISTENTE
    # --------------------------------------------------------

    answer = db.scalar(
        select(Answer)
        .where(
            Answer.evaluation_id ==
            evaluation.id,

            Answer.question_id ==
            question.id,
        )
    )

    if answer:

        answer.option_id = option.id

        answer.is_correct = bool(
            option.is_correct
        )

    else:

        answer = Answer(
            evaluation_id=
                evaluation.id,

            question_id=
                question.id,

            option_id=
                option.id,

            is_correct=
                bool(option.is_correct),
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

        "is_correct":
            answer.is_correct,
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

    if evaluation.completed_at:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya fue finalizada.",
        )

    if data.current_question >= evaluation.total_questions:
        raise HTTPException(
            status_code=400,
            detail="La pregunta indicada no es válida.",
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

    questions_list = db.scalars(
        select(Question)
        .order_by(Question.number)
    ).all()

    total = len(
        questions_list
    )

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
        question.number
        for question in questions_list
        if question.id
        not in answers_by_question
    ]

    if unanswered:
        raise HTTPException(
            status_code=400,
            detail=(
                "Debes responder todas las preguntas. "
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

    correct = sum(
        1
        for answer in answers
        if answer.is_correct
    )

    score = round(
        (correct / total) * 100
    )

    # --------------------------------------------------------
    # GUARDAR RESULTADO
    # --------------------------------------------------------

    evaluation.correct_answers = correct

    evaluation.total_questions = total

    evaluation.score = score

    evaluation.completed_at = (
        datetime.now(timezone.utc)
    )

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
    }