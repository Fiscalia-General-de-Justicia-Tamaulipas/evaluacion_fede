from datetime import datetime, timezone
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Boolean, DateTime, ForeignKey, Integer, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./evaluacion.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass
class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list["Option"]] = relationship(back_populates="question", cascade="all, delete-orphan", order_by="Option.position")
class Option(Base):
    __tablename__ = "options"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    letter: Mapped[str] = mapped_column(String(2))
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer)
    question: Mapped[Question] = relationship(back_populates="options")
class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(120))
    paternal_surname: Mapped[str] = mapped_column(String(120))
    maternal_surname: Mapped[str] = mapped_column(String(120))
class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    video_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_answers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer)
class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    option_id: Mapped[int] = mapped_column(ForeignKey("options.id"))
    is_correct: Mapped[bool] = mapped_column(Boolean)

Base.metadata.create_all(engine)

def seed():
    with SessionLocal() as db:
        if db.scalar(select(Question.id).limit(1)): return
        data = [
          (1,"En qué Ley encontramos los Delitos Electorales.",[('a','Ley General de Partidos Políticos.',False),('b','Ley General en Materia de Delitos Electorales.',True),('c','Ley General de Medios de Impugnación en Materia Electoral.',False)]),
          (2,"Es la Autoridad Electoral encargada de Organizar las elecciones en el Estado de Tamaulipas.",[('a','Instituto Electoral de Tamaulipas (IETAM).',True),('b','Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).',False),('c','Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).',False),('d','Instituto Nacional Electoral (INE).',False)]),
          (3,"Es la Autoridad Electoral que tiene como principal atribución conocer y resolver los medios de impugnación en materia electoral en el Estado de Tamaulipas.",[('a','Instituto Electoral de Tamaulipas (IETAM).',False),('b','Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).',True),('c','Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).',False)]),
          (4,"Es la Autoridad Electoral que tiene como principal atribución atender e investigar los delitos en materia electoral en el Estado de Tamaulipas.",[('a','Instituto Electoral de Tamaulipas (IETAM).',False),('b','Tribunal Electoral del Estado de Tamaulipas (TRIELTAM).',False),('c','Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE).',True)]),
          (5,"Es una de las formas de gobierno en las cuales se ejerce su soberanía eligiendo a sus gobernantes mediante el voto universal, libre y secreto.",[('a','Democracia',True),('b','Monarquía',False),('c','Dictadura',False)]),
          (6,"Es un derecho consagrado en el artículo 35 de la Constitución Política de los Estados Unidos Mexicanos que implica que cada ciudadana o ciudadano puede participar en elegir a sus representantes al emitir su voto. Este derecho va más allá de la elección de representantes y también se ejerce a través de otros mecanismos participativos de la democracia, tales como las consultas populares.",[('a','Voto activo.',True),('b','Voto pasivo.',False)]),
          (7,"El derecho de solicitar el registro de candidatos ante la autoridad electoral corresponde a los partidos políticos, así como a los ciudadanos que soliciten su registro de manera independiente y cumplan con los requisitos, condiciones y términos que determine la legislación, este derecho consagrado en el numeral 35 de la Constitución Política de los Estados Unidos Mexicanos se le conoce como:",[('a','Voto activo.',False),('b','Voto pasivo.',True)]),
          (8,"Es el conjunto de actos realizados en fases y que la Constitución y la Ley General de Instituciones y Procedimientos Electorales mandatan a las autoridades electorales, los partidos políticos y los ciudadanos para renovar periódicamente a los integrantes de los Poderes Legislativos y Ejecutivo federal y de las entidades federativas, así como de los ayuntamientos en los estados de la República y de las alcaldías en la Ciudad de México.",[('a','Proceso Legislativo.',False),('b','Proceso Electoral.',True),('c','Proceso Penal.',False)]),
          (9,"Son los comicios federal y local, que coinciden exactamente en la fecha prefijada en la Legislación Electoral de un Estado y en la Ley General de Instituciones y Procedimientos Electorales, en este tipo de proceso electoral se eligen cargos de elección popular locales y federales.",[('a','Proceso electoral extraordinario.',False),('b','Proceso electoral ordinario.',False),('c','Proceso electoral concurrente.',True)]),
          (10,"Es el periodo que comprende los tres días previos a la Jornada Electoral y concluye con la clausura de las casillas durante este periodo no está permitido realizar actos públicos de campaña, propaganda o proselitismo electoral publicar y difundir propaganda gubernamental.",[('a','Precampaña',False),('b','Veda electoral',True),('c','Campaña',False)]),
        ]
        for n,text,opts in data:
            q=Question(number=n,text=text); db.add(q); db.flush()
            for pos,(letter,opt,correct) in enumerate(opts,1): db.add(Option(question_id=q.id,letter=letter,text=opt,is_correct=correct,position=pos))
        db.commit()
seed()

app=FastAPI(title="Evaluación FEDE - FGJ Tamaulipas", version="1.0.0")
origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(',')
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
class ParticipantIn(BaseModel):
    first_name: str=Field(min_length=2,max_length=120); paternal_surname: str=Field(min_length=2,max_length=120); maternal_surname: str=Field(min_length=2,max_length=120)
class StartIn(ParticipantIn): pass
class AnswerIn(BaseModel): question_id:int; option_id:int
class FinishIn(BaseModel): answers:list[AnswerIn]=Field(min_length=10,max_length=10)

@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/questions')
def questions(db:Session=Depends(get_db)):
    qs=db.scalars(select(Question).order_by(Question.number)).all()
    return [{'id':q.id,'number':q.number,'text':q.text,'options':[{'id':o.id,'letter':o.letter,'text':o.text} for o in q.options]} for q in qs]
@app.post('/api/evaluations/start')
def start(data:StartIn,db:Session=Depends(get_db)):
    p=Participant(**data.model_dump()); db.add(p); db.flush()
    e=Evaluation(participant_id=p.id,video_completed=False,started_at=datetime.now(timezone.utc),total_questions=db.query(Question).count()); db.add(e); db.commit(); db.refresh(e)
    return {'evaluation_id':e.id,'participant_id':p.id}
@app.post('/api/evaluations/{evaluation_id}/video-completed')
def video_completed(evaluation_id:int,db:Session=Depends(get_db)):
    e=db.get(Evaluation,evaluation_id)
    if not e: raise HTTPException(404,'Evaluación no encontrada')
    e.video_completed=True; db.commit(); return {'video_completed':True}
@app.post('/api/evaluations/{evaluation_id}/finish')
def finish(evaluation_id:int,data:FinishIn,db:Session=Depends(get_db)):
    e=db.get(Evaluation,evaluation_id)
    if not e: raise HTTPException(404,'Evaluación no encontrada')
    if not e.video_completed: raise HTTPException(400,'El video debe haberse completado antes de contestar la evaluación.')
    if e.completed_at: raise HTTPException(409,'La evaluación ya fue finalizada.')
    correct=0
    for item in data.answers:
        q=db.get(Question,item.question_id); o=db.get(Option,item.option_id)
        if not q or not o or o.question_id!=q.id: raise HTTPException(400,'Respuesta inválida.')
        ok=bool(o.is_correct); correct+=ok; db.add(Answer(evaluation_id=e.id,question_id=q.id,option_id=o.id,is_correct=ok))
    e.correct_answers=correct; e.score=round(correct/e.total_questions*100); e.completed_at=datetime.now(timezone.utc); db.commit()
    return {'score':e.score,'correct_answers':correct,'total_questions':e.total_questions}
