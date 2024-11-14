# backend/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="funcionario")  # 'funcionario' ou 'supervisor'

class RMARequest(Base):
    __tablename__ = "rma_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    defect_type = Column(String)
    status = Column(String, default="Pendente")  # Status inicial
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")