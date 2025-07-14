from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker, Session

# Database setup
DATABASE_URL = "sqlite:///./kpa.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------------------
# Database Models
# ---------------------------
class KPA_DB(Base):
    __tablename__ = "kpas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    kras = relationship("KRA_DB", back_populates="kpa", cascade="all, delete")


class KRA_DB(Base):
    __tablename__ = "kras"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    kpa_id = Column(Integer, ForeignKey("kpas.id"))
    kpa = relationship("KPA_DB", back_populates="kras")
    tasks = relationship("Task_DB", back_populates="kra", cascade="all, delete")


class Task_DB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    kra_id = Column(Integer, ForeignKey("kras.id"))
    kra = relationship("KRA_DB", back_populates="tasks")


# Create tables
Base.metadata.create_all(bind=engine)

# ---------------------------
# Pydantic Models (Input & Output)
# ---------------------------

# Input Models
class KPAInput(BaseModel):
    name: str

class KRAInput(BaseModel):
    name: str

class TaskInput(BaseModel):
    name: str

# Output Models
class Task(BaseModel):
    id: Optional[int]
    name: str

    model_config = {
        "from_attributes": True
    }

class KRA(BaseModel):
    id: Optional[int]
    name: str
    tasks: List[Task] = []

    model_config = {
        "from_attributes": True
    }

class KPA(BaseModel):
    id: Optional[int]
    name: str
    kras: List[KRA] = []

    model_config = {
        "from_attributes": True
    }

# ---------------------------
# Routes
# ---------------------------

# KPA Routes
@app.post("/kpa/", response_model=KPA)
def create_kpa(kpa: KPAInput, db: Session = Depends(get_db)):
    db_kpa = KPA_DB(name=kpa.name)
    db.add(db_kpa)
    db.commit()
    db.refresh(db_kpa)
    return db_kpa

@app.get("/kpa/", response_model=List[KPA])
def get_kpas(db: Session = Depends(get_db)):
    return db.query(KPA_DB).all()

@app.get("/kpa/{kpa_id}", response_model=KPA)
def get_kpa(kpa_id: int, db: Session = Depends(get_db)):
    kpa = db.query(KPA_DB).filter(KPA_DB.id == kpa_id).first()
    if not kpa:
        raise HTTPException(status_code=404, detail="KPA not found")
    return kpa

@app.delete("/kpa/{kpa_id}")
def delete_kpa(kpa_id: int, db: Session = Depends(get_db)):
    kpa = db.query(KPA_DB).filter(KPA_DB.id == kpa_id).first()
    if not kpa:
        raise HTTPException(status_code=404, detail="KPA not found")
    db.delete(kpa)
    db.commit()
    return {"detail": "KPA deleted"}

# KRA Routes
@app.post("/kra/", response_model=KRA)
def create_kra(kra: KRAInput, kpa_id: int, db: Session = Depends(get_db)):
    db_kra = KRA_DB(name=kra.name, kpa_id=kpa_id)
    db.add(db_kra)
    db.commit()
    db.refresh(db_kra)
    return db_kra

@app.get("/kra/", response_model=List[KRA])
def get_kras(db: Session = Depends(get_db)):
    return db.query(KRA_DB).all()

# Task Routes
@app.post("/task/", response_model=Task)
def create_task(task: TaskInput, kra_id: int, db: Session = Depends(get_db)):
    db_task = Task_DB(name=task.name, kra_id=kra_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/task/", response_model=List[Task])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task_DB).all()

@app.delete("/kra/{kra_id}")
def delete_kra(kra_id: int):
    kra = db.query(KRA_DB).filter(KRA_DB.id == kra_id).first()
    if not kra:
        raise HTTPException(status_code=404, detail="KRA not found")
    db.delete(kra)
    db.commit()
    return {"detail": "KRA deleted"}
