from datetime import datetime, timedelta, timezone

import os

import time

from pathlib import Path

from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import OAuth2PasswordBearer

from fastapi.exceptions import RequestValidationError

from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field, EmailStr

from passlib.context import CryptContext

from jose import JWTError, jwt

from sqlalchemy import (

    create_engine,

    String,

    Boolean,

    DateTime,

    ForeignKey,

    Integer,

    Text,

    UniqueConstraint,

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

# Clave para firmar los tokens JWT. En producción DEBE definirse en el .env

# con un valor largo y aleatorio (por ejemplo: openssl rand -hex 32).

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))



# ============================================================

# BASE SQLALCHEMY

# ============================================================

class Base(DeclarativeBase):

    pass



# ============================================================

# MODELOS

# ============================================================

class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    municipalities: Mapped[list["Municipality"]] = relationship(
        back_populates="state",
        cascade="all, delete-orphan",
    )


class Municipality(Base):
    __tablename__ = "municipalities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_other: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    state: Mapped[State] = relationship(back_populates="municipalities")
    users: Mapped[list["User"]] = relationship(back_populates="municipality")

    __table_args__ = (
        UniqueConstraint("state_id", "name", name="uq_municipality_state_name"),
    )


class Gender(Base):
    __tablename__ = "genders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="gender")


class AgeRange(Base):
    __tablename__ = "age_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="age_range")


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="occupation")


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="sector")


class YesNoOption(Base):
    __tablename__ = "yes_no_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


class EducationLevel(Base):
    __tablename__ = "education_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="education_level")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    paternal_surname: Mapped[str] = mapped_column(String(120), nullable=False)
    maternal_surname: Mapped[str] = mapped_column(String(120), nullable=False)

    email: Mapped[str] = mapped_column(String(190), unique=True, nullable=False, index=True)
    curp: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)


    # Ubicación.
    municipality_id: Mapped[int | None] = mapped_column(
        ForeignKey("municipalities.id"), nullable=True
    )
    municipality_other: Mapped[str | None] = mapped_column(String(150), nullable=True)
    municipality_other_state: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Perfil.
    gender_id: Mapped[int | None] = mapped_column(
        ForeignKey("genders.id"), nullable=True
    )
    gender_other: Mapped[str | None] = mapped_column(String(100), nullable=True)

    age_range_id: Mapped[int | None] = mapped_column(
        ForeignKey("age_ranges.id"), nullable=True
    )

    occupation_id: Mapped[int | None] = mapped_column(
        ForeignKey("occupations.id"), nullable=True
    )
    occupation_other: Mapped[str | None] = mapped_column(String(200), nullable=True)

    sector_id: Mapped[int | None] = mapped_column(
        ForeignKey("sectors.id"), nullable=True
    )

    # Respuestas Sí/No. Se mantienen como IDs de catálogo.
    indigenous_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"), nullable=True
    )
    afro_mexican_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"), nullable=True
    )
    disability_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"), nullable=True
    )
    lgbtttiq_id: Mapped[int | None] = mapped_column(
        ForeignKey("yes_no_options.id"), nullable=True
    )

    education_level_id: Mapped[int | None] = mapped_column(
        ForeignKey("education_levels.id"), nullable=True
    )

    municipality: Mapped[Municipality | None] = relationship(back_populates="users")
    gender: Mapped[Gender | None] = relationship(back_populates="users")
    age_range: Mapped[AgeRange | None] = relationship(back_populates="users")
    occupation: Mapped[Occupation | None] = relationship(back_populates="users")
    sector: Mapped[Sector | None] = relationship(back_populates="users")
    education_level: Mapped[EducationLevel | None] = relationship(back_populates="users")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="user")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.paternal_surname} {self.maternal_surname}".strip()


class Question(Base):

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    options: Mapped[list["Option"]] = relationship(

        back_populates="question",

        cascade="all, delete-orphan",

        order_by="Option.position",

    )



class Option(Base):

    __tablename__ = "options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)

    letter: Mapped[str] = mapped_column(String(2), nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped[Question] = relationship(back_populates="options")



class Evaluation(Base):

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="evaluations")

    video_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    correct_answers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)



class Answer(Base):

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"), nullable=False)

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)

    option_id: Mapped[int] = mapped_column(ForeignKey("options.id"), nullable=False)

    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)



# ============================================================

# DATABASE URL (admin helper para crear la BD si no existe)

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

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)



# ============================================================

# DATABASE

# ============================================================

def ensure_database_exists() -> None:

    database_name = urlparse(DATABASE_URL).path.lstrip("/")

    if not database_name:

        return

    admin_url = get_admin_database_url(DATABASE_URL)

    admin_engine = create_engine(admin_url, pool_pre_ping=True)

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



def wait_for_database(max_attempts: int = 30, delay_seconds: int = 2) -> None:

    last_error = None

    for attempt in range(max_attempts):

        try:

            with engine.connect() as connection:

                connection.execute(text("SELECT 1"))

            print("✓ Conexión a MySQL establecida.")

            return

        except Exception as exc:

            last_error = exc

            print(f"Esperando MySQL... intento {attempt + 1}/{max_attempts}")

            time.sleep(delay_seconds)

    raise RuntimeError("No se pudo conectar a la base de datos MySQL.") from last_error



# ============================================================

# SEED

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

# No se inventan opciones de ocupación porque el requerimiento recibido
# no proporciona el catálogo. Se crea la tabla para que el catálogo pueda
# poblarse posteriormente sin cambiar la estructura de users.
# ============================================================
# CATÁLOGO DE OCUPACIONES
# ============================================================

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

def seed_catalog_simple(db: Session, model, names: list[str]) -> None:
    existing = set(db.scalars(select(model.name)))
    for name in names:
        if name not in existing:
            db.add(model(name=name))


def seed_profile_catalogs() -> None:
    with SessionLocal() as db:
        # Estados / municipios.
        tamaulipas = db.scalar(
            select(State).where(State.name == "Tamaulipas")
        )
        if not tamaulipas:
            tamaulipas = State(name="Tamaulipas")
            db.add(tamaulipas)
            db.flush()

        existing_municipalities = {
            municipality.name
            for municipality in db.scalars(
                select(Municipality).where(
                    Municipality.state_id == tamaulipas.id
                )
            )
        }

        for name in TAMAULIPAS_MUNICIPALITIES:
            if name not in existing_municipalities:
                db.add(
                    Municipality(
                        state_id=tamaulipas.id,
                        name=name,
                        is_other=False,
                    )
                )

        seed_catalog_simple(db, Gender, GENDER_NAMES)
        seed_catalog_simple(db, AgeRange, AGE_RANGE_NAMES)
        seed_catalog_simple(db, Occupation, OCCUPATION_NAMES)
        seed_catalog_simple(db, Sector, SECTOR_NAMES)
        seed_catalog_simple(db, YesNoOption, YES_NO_NAMES)
        seed_catalog_simple(db, EducationLevel, EDUCATION_LEVEL_NAMES)

        db.commit()

    print("✓ Catálogos de perfil, estados y municipios verificados.")


def seed_questions() -> None:

    with SessionLocal() as db:

        existing_question = db.scalar(select(Question.id).limit(1))

        if existing_question:

            print("✓ Las preguntas ya existen. Seed omitido.")

            return

        print("Insertando preguntas y respuestas...")

        data = [

            (

                1,

                "En qué Ley encontramos los Delitos Electorales.",

                [

                    ("a", "Ley General de Partidos Políticos.", False),

                    ("b", "Ley General en Materia de Delitos Electorales.", True),

                    ("c", "Ley General de Medios de Impugnación en Materia Electoral.", False),

                ],

            ),

            (

                2,

                "Es la Autoridad Electoral encargada de Organizar las elecciones en el Estado de Tamaulipas.",

                [

                    ("a", "Instituto Electoral de Tamaulipas (IETAM).", True),

                    ("b", "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).", False),

                    ("c", "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).", False),

                    ("d", "Instituto Nacional Electoral (INE).", False),

                ],

            ),

            (

                3,

                "Es la Autoridad Electoral que tiene como principal atribución conocer y resolver los medios de impugnación en materia electoral en el Estado de Tamaulipas.",

                [

                    ("a", "Instituto Electoral de Tamaulipas (IETAM).", False),

                    ("b", "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).", True),

                    ("c", "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).", False),

                ],

            ),

            (

                4,

                "Es la Autoridad Electoral que tiene como principal atribución atender e investigar los delitos en materia electoral en el Estado de Tamaulipas.",

                [

                    ("a", "Instituto Electoral de Tamaulipas (IETAM).", False),

                    ("b", "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).", False),

                    ("c", "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).", True),

                ],

            ),

            (

                5,

                "Es una de las formas de gobierno en las cuales se ejerce su soberanía eligiendo a sus gobernantes mediante el voto universal, libre y secreto.",

                [

                    ("a", "Democracia", True),

                    ("b", "Monarquía", False),

                    ("c", "Dictadura", False),

                ],

            ),

            (

                6,

                "Es un derecho consagrado en el artículo 35 de la Constitución Política de los Estados Unidos Mexicanos que implica que cada ciudadana o ciudadano puede participar en elegir a sus representantes al emitir su voto. Este derecho va más allá de la elección de representantes y también se ejerce a través de otros mecanismos participativos de la democracia, tales como las consultas populares.",

                [

                    ("a", "Voto activo.", True),

                    ("b", "Voto pasivo.", False),

                ],

            ),

            (

                7,

                "El derecho de solicitar el registro de candidatos ante la autoridad electoral corresponde a los partidos políticos, así como a los ciudadanos que soliciten su registro de manera independiente y cumplan con los requisitos, condiciones y términos que determine la legislación, este derecho consagrado en el numeral 35 de la Constitución Política de los Estados Unidos Mexicanos se le conoce como:",

                [

                    ("a", "Voto activo.", False),

                    ("b", "Voto pasivo.", True),

                ],

            ),

            (

                8,

                "Es el conjunto de actos realizados en fases y que la Constitución y la Ley General de Instituciones y Procedimientos Electorales mandatan a las autoridades electorales, los partidos políticos y los ciudadanos para renovar periódicamente a los integrantes de los Poderes Legislativos y Ejecutivo federal y de las entidades federativas, así como de los ayuntamientos en los estados de la República y de las alcaldías en la Ciudad de México.",

                [

                    ("a", "Proceso Legislativo.", False),

                    ("b", "Proceso Electoral.", True),

                    ("c", "Proceso Penal.", False),

                ],

            ),

            (

                9,

                "Son los comicios federal y local, que coinciden exactamente en la fecha prefijada en la Legislación Electoral de un Estado y en la Ley General de Instituciones y Procedimientos Electorales, en este tipo de proceso electoral se eligen cargos de elección popular locales y federales.",

                [

                    ("a", "Proceso electoral extraordinario.", False),

                    ("b", "Proceso electoral ordinario.", False),

                    ("c", "Proceso electoral concurrente.", True),

                ],

            ),

            (

                10,

                "Es el periodo que comprende los tres días previos a la Jornada Electoral y concluye con la clausura de las casillas durante este periodo no está permitido realizar actos públicos de campaña, propaganda o proselitismo electoral publicar y difundir propaganda gubernamental.",

                [

                    ("a", "Precampaña", False),

                    ("b", "Veda electoral", True),

                    ("c", "Campaña", False),

                ],

            ),

        ]

        for number, question_text, options in data:

            question = Question(number=number, text=question_text)

            db.add(question)

            db.flush()

            for position, (letter, option_text, correct) in enumerate(options, start=1):

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

# ============================================================
# COMPATIBILIDAD / MIGRACIÓN LIGERA
# ============================================================
def ensure_user_profile_columns() -> None:
    """
    Base.metadata.create_all() no agrega columnas a una tabla users existente.
    Esta migración ligera agrega únicamente las columnas nuevas que falten.
    Es útil mientras el proyecto no utiliza Alembic.
    """
    from sqlalchemy import inspect

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    columns_to_add = {
        "municipality_id": "INT NULL",
        "municipality_other": "VARCHAR(150) NULL",
        "municipality_other_state": "VARCHAR(150) NULL",
        "gender_id": "INT NULL",
        "gender_other": "VARCHAR(100) NULL",
        "age_range_id": "INT NULL",
        "occupation_id": "INT NULL",
        "occupation_other": "VARCHAR(200) NULL",
        "sector_id": "INT NULL",
        "indigenous_id": "INT NULL",
        "afro_mexican_id": "INT NULL",
        "disability_id": "INT NULL",
        "lgbtttiq_id": "INT NULL",
        "education_level_id": "INT NULL",
    }

    with engine.begin() as connection:
        for column_name, definition in columns_to_add.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE users ADD COLUMN {column_name} {definition}"
                    )
                )
                print(f"✓ Columna users.{column_name} agregada.")


def ensure_user_foreign_keys() -> None:
    """Agrega FKs nuevas si no existen en una BD previamente creada."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_fks = inspector.get_foreign_keys("users")
    existing_pairs = {
        (
            fk.get("referred_table"),
            tuple(fk.get("constrained_columns") or []),
        )
        for fk in existing_fks
    }

    foreign_keys = [
        (
            "fk_users_municipality",
            "municipality_id",
            "municipalities",
            "id",
        ),
        (
            "fk_users_gender",
            "gender_id",
            "genders",
            "id",
        ),
        (
            "fk_users_age_range",
            "age_range_id",
            "age_ranges",
            "id",
        ),
        (
            "fk_users_occupation",
            "occupation_id",
            "occupations",
            "id",
        ),
        (
            "fk_users_sector",
            "sector_id",
            "sectors",
            "id",
        ),
        (
            "fk_users_indigenous",
            "indigenous_id",
            "yes_no_options",
            "id",
        ),
        (
            "fk_users_afro_mexican",
            "afro_mexican_id",
            "yes_no_options",
            "id",
        ),
        (
            "fk_users_disability",
            "disability_id",
            "yes_no_options",
            "id",
        ),
        (
            "fk_users_lgbtttiq",
            "lgbtttiq_id",
            "yes_no_options",
            "id",
        ),
        (
            "fk_users_education_level",
            "education_level_id",
            "education_levels",
            "id",
        ),
    ]

    with engine.begin() as connection:
        for constraint_name, column_name, referred_table, referred_column in foreign_keys:
            pair = (referred_table, (column_name,))
            if pair in existing_pairs:
                continue

            try:
                connection.execute(
                    text(
                        f"ALTER TABLE users "
                        f"ADD CONSTRAINT {constraint_name} "
                        f"FOREIGN KEY ({column_name}) "
                        f"REFERENCES {referred_table} ({referred_column})"
                    )
                )
                print(f"✓ FK users.{column_name} -> {referred_table}.id agregada.")
            except Exception as exc:
                # Si una BD existente tiene una condición particular que impide
                # agregar la FK, no bloqueamos el arranque. La validación del
                # endpoint de registro sigue protegiendo los IDs recibidos.
                print(
                    f"Aviso: no se pudo agregar la FK de users.{column_name}: {exc}"
                )


def initialize_database() -> None:

    print("Inicializando base de datos...")

    ensure_database_exists()

    wait_for_database()

    print("Creando tablas...")

    Base.metadata.create_all(bind=engine)

    print("✓ Tablas verificadas/creadas.")

    # Compatibilidad con instalaciones existentes.
    ensure_user_profile_columns()
    ensure_user_foreign_keys()

    seed_profile_catalogs()
    seed_questions()

    print("✓ Base de datos inicializada correctamente.")



# ============================================================

# FASTAPI

# ============================================================

app = FastAPI(

    title="Evaluación FEDE - FGJ Tamaulipas",

    version="2.0.0",

)



# ============================================================

# CORS

# ============================================================

origins = [

    origin.strip()

    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",")

    if origin.strip()

]

app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)





ERROR_MESSAGES_ES = {

    "missing": "Este campo es obligatorio.",

    "string_too_short": "El valor es demasiado corto.",

    "string_too_long": "El valor es demasiado largo.",

    "value_error": "El valor ingresado no es válido.",

}



def translate_error(err: dict) -> str:

    field = err["loc"][-1] if err.get("loc") else ""

    error_type = err.get("type", "")

    if field == "email" and ("email" in error_type or "value_error" in error_type):

        return "El correo electrónico no es válido. Debe incluir un @, por ejemplo: nombre@dominio.com"

    if field == "password":

        if error_type == "string_too_short":

            return "La contraseña debe tener al menos 8 caracteres."

        if error_type == "string_too_long":

            return "La contraseña es demasiado larga."

    if field == "curp":

        return "La CURP debe tener exactamente 18 caracteres."

    return ERROR_MESSAGES_ES.get(error_type, "Uno de los campos no es válido.")



@app.exception_handler(RequestValidationError)

async def validation_exception_handler(request, exc: RequestValidationError):

    errors = exc.errors()

    message = translate_error(errors[0]) if errors else "Datos inválidos."

    return JSONResponse(

        status_code=422,

        content={"detail": message},

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

# SEGURIDAD / AUTH

# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)



def hash_password(password: str) -> str:

    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:

    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(subject: str) -> str:

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {"sub": subject, "exp": expire}

    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)



def get_current_user(

    token: str | None = Depends(oauth2_scheme),

    db: Session = Depends(get_db),

) -> User:

    credentials_exception = HTTPException(

        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="No se pudo validar la sesión.",

        headers={"WWW-Authenticate": "Bearer"},

    )

    if not token:

        raise credentials_exception

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        user_id = payload.get("sub")

        if user_id is None:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = db.get(User, int(user_id))

    if not user:

        raise credentials_exception

    return user



# ============================================================

# SCHEMAS

# ============================================================

class CatalogItemOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MunicipalityOut(BaseModel):
    id: int
    state_id: int
    name: str
    is_other: bool

    class Config:
        from_attributes = True


class StateOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=2, max_length=120)
    paternal_surname: str = Field(min_length=2, max_length=120)
    maternal_surname: str = Field(min_length=2, max_length=120)

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    curp: str = Field(min_length=18, max_length=18)

    municipality_id: int | None = None
    municipality_other: str | None = Field(default=None, max_length=150)
    municipality_other_state: str | None = Field(default=None, max_length=150)

    gender_id: int | None = None
    gender_other: str | None = Field(default=None, max_length=100)

    age_range_id: int | None = None

    occupation_id: int | None = None
    occupation_other: str | None = Field(default=None, max_length=200)

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
    email: EmailStr
    curp: str

    #institution: InstitutionOut

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

    class Config:
        from_attributes = True


class TokenOut(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserOut



class AnswerIn(BaseModel):

    question_id: int

    option_id: int



class FinishIn(BaseModel):

    answers: list[AnswerIn] = Field(min_length=1)



# ============================================================

# HEALTH

# ============================================================

@app.get("/api/health")

def health():

    return {"status": "ok"}



# ============================================================

# INSTITUTIONS

# ============================================================

"""
@app.get("/api/institutions", response_model=list[InstitutionOut])
def list_institutions(db: Session = Depends(get_db)):
    return db.scalars(select(Institution).order_by(Institution.name)).all()
"""



# ============================================================
# CATALOGS
# ============================================================
@app.get("/api/catalogs/states", response_model=list[StateOut])
def list_states(db: Session = Depends(get_db)):
    return db.scalars(select(State).order_by(State.name)).all()


@app.get("/api/catalogs/municipalities", response_model=list[MunicipalityOut])
def list_municipalities(
    state_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Municipality)
    if state_id is not None:
        query = query.where(Municipality.state_id == state_id)
    return db.scalars(query.order_by(Municipality.name)).all()


@app.get("/api/catalogs/genders", response_model=list[CatalogItemOut])
def list_genders(db: Session = Depends(get_db)):
    return db.scalars(select(Gender).order_by(Gender.id)).all()


@app.get("/api/catalogs/age-ranges", response_model=list[CatalogItemOut])
def list_age_ranges(db: Session = Depends(get_db)):
    return db.scalars(select(AgeRange).order_by(AgeRange.id)).all()


@app.get("/api/catalogs/occupations", response_model=list[CatalogItemOut])
def list_occupations(db: Session = Depends(get_db)):
    return db.scalars(select(Occupation).order_by(Occupation.name)).all()


@app.get("/api/catalogs/sectors", response_model=list[CatalogItemOut])
def list_sectors(db: Session = Depends(get_db)):
    return db.scalars(select(Sector).order_by(Sector.id)).all()


@app.get("/api/catalogs/yes-no", response_model=list[CatalogItemOut])
def list_yes_no(db: Session = Depends(get_db)):
    return db.scalars(select(YesNoOption).order_by(YesNoOption.id)).all()


@app.get("/api/catalogs/education-levels", response_model=list[CatalogItemOut])
def list_education_levels(db: Session = Depends(get_db)):
    return db.scalars(select(EducationLevel).order_by(EducationLevel.id)).all()


# AUTH

# ============================================================

@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    curp = data.curp.upper().strip()

    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(
            status_code=409,
            detail="Ya existe una cuenta con ese correo electrónico.",
        )

    if db.scalar(select(User.id).where(User.curp == curp)):
        raise HTTPException(
            status_code=409,
            detail="Ya existe una cuenta registrada con esa CURP.",
        )

    """
        institution = db.get(Institution, data.institution_id)
        if not institution:
            raise HTTPException(status_code=400, detail="Institución inválida.")

    """

    # --------------------------------------------------------
    # Validación de catálogos
    # --------------------------------------------------------
    if data.municipality_id is not None:
        municipality = db.get(Municipality, data.municipality_id)
        if not municipality:
            raise HTTPException(status_code=400, detail="Municipio inválido.")

    if data.gender_id is not None:
        if not db.get(Gender, data.gender_id):
            raise HTTPException(status_code=400, detail="Género inválido.")

    if data.age_range_id is not None:
        if not db.get(AgeRange, data.age_range_id):
            raise HTTPException(status_code=400, detail="Rango de edad inválido.")

    if data.occupation_id is not None:
        if not db.get(Occupation, data.occupation_id):
            raise HTTPException(status_code=400, detail="Ocupación inválida.")

    if data.sector_id is not None:
        if not db.get(Sector, data.sector_id):
            raise HTTPException(status_code=400, detail="Institución o sector inválido.")

    for field_name, label in [
        ("indigenous_id", "Auto adscripción indígena"),
        ("afro_mexican_id", "Auto adscripción afromexicana"),
        ("disability_id", "Discapacidad"),
        ("lgbtttiq_id", "Identificación LGBTTTIQ+"),
    ]:
        value = getattr(data, field_name)
        if value is not None and not db.get(YesNoOption, value):
            raise HTTPException(status_code=400, detail=f"{label}: opción inválida.")

    if data.education_level_id is not None:
        if not db.get(EducationLevel, data.education_level_id):
            raise HTTPException(status_code=400, detail="Grado de estudios inválido.")

    # --------------------------------------------------------
    # Reglas para "Otro"
    # --------------------------------------------------------
    if data.municipality_id is None:
        if not data.municipality_other or not data.municipality_other.strip():
            raise HTTPException(
                status_code=400,
                detail="Selecciona un municipio o especifica el municipio en Otro.",
            )

        if not data.municipality_other_state or not data.municipality_other_state.strip():
            raise HTTPException(
                status_code=400,
                detail="Especifica el estado cuando el municipio sea Otro.",
            )
    else:
        # Si se seleccionó un municipio del catálogo, no necesitamos los textos de Otro.
        data.municipality_other = None
        data.municipality_other_state = None

    if data.gender_id is not None:
        gender = db.get(Gender, data.gender_id)
        if gender and gender.name == "Otro":
            if not data.gender_other or not data.gender_other.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Especifica el género cuando seleccionas Otro.",
                )
        else:
            data.gender_other = None

    if data.occupation_id is not None:
        occupation = db.get(Occupation, data.occupation_id)
        if occupation and occupation.name == "Otro":
            if not data.occupation_other or not data.occupation_other.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Especifica la ocupación cuando seleccionas Otro.",
                )
        else:
            data.occupation_other = None

    user = User(
        first_name=data.first_name.strip(),
        paternal_surname=data.paternal_surname.strip(),
        maternal_surname=data.maternal_surname.strip(),
        email=email,
        curp=curp,
        hashed_password=hash_password(data.password),
        #institution_id=institution.id,

        municipality_id=data.municipality_id,
        municipality_other=(
            data.municipality_other.strip()
            if data.municipality_other
            else None
        ),
        municipality_other_state=(
            data.municipality_other_state.strip()
            if data.municipality_other_state
            else None
        ),

        gender_id=data.gender_id,
        gender_other=(
            data.gender_other.strip()
            if data.gender_other
            else None
        ),

        age_range_id=data.age_range_id,

        occupation_id=data.occupation_id,
        occupation_other=(
            data.occupation_other.strip()
            if data.occupation_other
            else None
        ),

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

    token = create_access_token(subject=str(user.id))
    return TokenOut(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@app.post("/api/auth/login", response_model=TokenOut)

def login(data: LoginIn, db: Session = Depends(get_db)):

    email = data.email.lower().strip()

    user = db.scalar(select(User).where(User.email == email))

    if not user or not verify_password(data.password, user.hashed_password):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Correo electrónico o contraseña incorrectos.",

        )

    token = create_access_token(subject=str(user.id))

    return TokenOut(access_token=token, user=UserOut.model_validate(user))



@app.get("/api/auth/me", response_model=UserOut)

def me(current_user: User = Depends(get_current_user)):

    return UserOut.model_validate(current_user)



# ============================================================

# QUESTIONS

# ============================================================

@app.get("/api/questions")

def questions(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    qs = db.scalars(select(Question).order_by(Question.number)).all()

    return [

        {

            "id": q.id,

            "number": q.number,

            "text": q.text,

            "options": [

                {"id": o.id, "letter": o.letter, "text": o.text}

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

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    total_questions = db.query(Question).count()

    evaluation = Evaluation(

        user_id=current_user.id,

        started_at=datetime.now(timezone.utc),

        total_questions=total_questions,

    )

    db.add(evaluation)

    db.commit()

    db.refresh(evaluation)

    return {

        "evaluation_id": evaluation.id,

        "user": UserOut.model_validate(current_user),

    }



# ============================================================

# VIDEO COMPLETED

# ============================================================

@app.post("/api/evaluations/{evaluation_id}/video-completed")

def video_completed(

    evaluation_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    evaluation = db.get(Evaluation, evaluation_id)

    if not evaluation or evaluation.user_id != current_user.id:

        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")

    evaluation.video_completed = True

    db.commit()

    return {"video_completed": True}



# ============================================================

# FINISH

# ============================================================

@app.post("/api/evaluations/{evaluation_id}/finish")

def finish(

    evaluation_id: int,

    data: FinishIn,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    evaluation = db.get(Evaluation, evaluation_id)

    if not evaluation or evaluation.user_id != current_user.id:

        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")

    if not evaluation.video_completed:

        raise HTTPException(

            status_code=400,

            detail="El video debe haberse completado antes de contestar la evaluación.",

        )

    if evaluation.completed_at:

        raise HTTPException(status_code=409, detail="La evaluación ya fue finalizada.")

    questions_list = db.scalars(select(Question).order_by(Question.number)).all()

    if len(data.answers) != len(questions_list):

        raise HTTPException(status_code=400, detail="Debes responder todas las preguntas.")

    correct = 0

    submitted_questions = set()

    for item in data.answers:

        if item.question_id in submitted_questions:

            raise HTTPException(

                status_code=400,

                detail="No puedes responder una pregunta más de una vez.",

            )

        submitted_questions.add(item.question_id)

        question = db.get(Question, item.question_id)

        option = db.get(Option, item.option_id)

        if not question or not option:

            raise HTTPException(status_code=400, detail="Respuesta inválida.")

        if option.question_id != question.id:

            raise HTTPException(

                status_code=400,

                detail="La opción no pertenece a la pregunta seleccionada.",

            )

        is_correct = bool(option.is_correct)

        if is_correct:

            correct += 1

        db.add(

            Answer(

                evaluation_id=evaluation.id,

                question_id=question.id,

                option_id=option.id,

                is_correct=is_correct,

            )

        )

    total = len(questions_list)

    score = round((correct / total) * 100) if total else 0

    evaluation.correct_answers = correct

    evaluation.total_questions = total

    evaluation.score = score

    evaluation.completed_at = datetime.now(timezone.utc)

    db.commit()

    return {

        "success": True,

        "message": "Evaluación registrada correctamente.",

    }