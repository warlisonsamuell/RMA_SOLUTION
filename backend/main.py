# from tkinter.tix import STATUS
# from fastapi import Depends, FastAPI, HTTPException
# from .rma import router as rma_router
# from .auth import create_access_token, router as auth_router
# from .database import engine
# from .models import Base
# from sqlalchemy.orm import Session
# from . import models, schemas, database
# from .schemas import UserCreate



# # Criar as tabelas no banco de dados
# Base.metadata.create_all(bind=engine)

# app = FastAPI()

# # Incluir as rotas
# app.include_router(rma_router, prefix="/rma", tags=["RMA"])
# app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# # Dependência para obter a sessão do banco
# def get_db():
#     db = database.SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Rota para criar uma solicitação de RMA
# @app.post("/rma/create", response_model=schemas.RMASuccess)
# def create_rma(request: schemas.RMARequest, db: Session = Depends(get_db)):
#     # Cria um novo objeto RMA
#     new_rma = models.RMARequest(
#         produto=request.produto,
#         defeito=request.defeito,
#         status=request.status
#     )
#     db.add(new_rma)
#     db.commit()
#     db.refresh(new_rma)
    
#     return schemas.RMASuccess(message="Solicitação de RMA registrada com sucesso!")


# @app.get("/rma/status")
# def get_rma_status(db: Session = Depends(get_db)):
#     rmas = db.query(models.RMARequest).all()
#     status_count = {
#         "pendente": sum(1 for rma in rmas if rma.status == "Pendente"),
#         "recebida": sum(1 for rma in rmas if rma.status == "Recebida"),
#         "em_teste": sum(1 for rma in rmas if rma.status == "Em Teste"),
#         "concluida": sum(1 for rma in rmas if rma.status == "Concluída"),
#     }
#     return status_count


# @app.post("/auth/login")
# def login(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(models.User).filter(models.User.username == user.username).first()
#     if db_user is None or not db_user.verify_password(user.password):  # Adapte conforme sua verificação de senha
#         raise HTTPException(status_code=STATUS.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    
#     access_token = create_access_token(data={"sub": db_user.username})
#     return {"access_token": access_token, "token_type": "bearer"}


# -----------------------------------------------------
# from fastapi import FastAPI, APIRouter, HTTPException, Depends
# from pydantic import BaseModel
# from sqlalchemy import create_engine, Column, Integer, String
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session

# # Definir a configuração do banco de dados
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:131156@localhost:5432/RMASOLUTION"

# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Definindo o modelo (RMARequest)
# class RMARequest(Base):
#     __tablename__ = 'rma_requests'

#     id = Column(Integer, primary_key=True, index=True)
#     produto = Column(String, index=True)
#     defeito = Column(String)
#     status = Column(String)

# # Criando o banco de dados (caso não exista)
# Base.metadata.create_all(bind=engine)

# # Definindo o esquema para validação de dados (Pydantic)
# class RMARequestCreate(BaseModel):
#     produto: str
#     defeito: str
#     status: str

# class RMASuccess(BaseModel):
#     message: str

# # Instanciando o FastAPI
# app = FastAPI()

# # Função para obter a sessão de banco de dados
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Definindo o Router para as rotas da RMA
# router = APIRouter()

# # Endpoint para criar uma solicitação RMA
# @router.post("/rma/create", response_model=RMASuccess)
# def create_rma(rma: RMARequestCreate, db: Session = Depends(get_db)):
#     db_rma = RMARequest(produto=rma.produto, defeito=rma.defeito, status=rma.status)
#     db.add(db_rma)
#     db.commit()
#     db.refresh(db_rma)
#     return {"message": "Solicitação RMA criada com sucesso"}

# # Endpoint para consultar todas as solicitações RMA
# @router.get("/rma/status", response_model=list[RMARequestCreate])
# def get_rma_status(db: Session = Depends(get_db)):
#     rmas = db.query(RMARequest).all()
#     return rmas

# # Registrando o Router no aplicativo FastAPI
# app.include_router(router)





from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Union

# Configuração do banco de dados
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:131156@localhost:5432/RMASOLUTION"

# Criando o engine e a sessão do banco
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criando a base para as tabelas
Base = declarative_base()

# Definindo o modelo do usuário
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# Definindo o modelo da solicitação de RMA
class RMARequest(Base):
    __tablename__ = 'rma_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    produto = Column(String)
    defeito = Column(String)
    status = Column(String)

# Criando a aplicação FastAPI
app = FastAPI()

# Configuração do PassLib para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Função para gerar o hash da senha
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Função para verificar a senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Função para criar o token de acesso
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Criar as tabelas no banco de dados (caso ainda não existam)
Base.metadata.create_all(bind=engine)

# Rota de registro de usuário
@app.post("/auth/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    
    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Usuário criado com sucesso"}

# Rota de login
@app.post("/auth/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    
    if db_user is None or not verify_password(password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Rota para criar uma solicitação de RMA
@app.post("/rma/create")
def create_rma(produto: str, defeito: str, status: str, db: Session = Depends(get_db)):
    new_rma = RMARequest(produto=produto, defeito=defeito, status=status)
    db.add(new_rma)
    db.commit()
    db.refresh(new_rma)
    
    return {"message": "Solicitação de RMA registrada com sucesso!"}

# Rota para obter o status das solicitações de RMA
@app.get("/rma/status")
def get_rma_status(db: Session = Depends(get_db)):
    rmas = db.query(RMARequest).all()
    status_count = {
        "pendente": sum(1 for rma in rmas if rma.status == "Pendente"),
        "recebida": sum(1 for rma in rmas if rma.status == "Recebida"),
        "em_teste": sum(1 for rma in rmas if rma.status == "Em Teste"),
        "concluida": sum(1 for rma in rmas if rma.status == "Concluída"),
    }
    return status_count
