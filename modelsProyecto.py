from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, Text
from sqlalchemy.orm import relationship
from databaseProyecto import Base
from datetime import datetime 
from pydantic import BaseModel

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    es_admin = Column(Boolean, default=False)
    
    imagenes = relationship("Imagen", back_populates="usuario", cascade="all, delete-orphan") 
    historial = relationship("HistorialChat", back_populates="usuario")

class UsuarioSchema(BaseModel):
    username: str
    es_admin: bool = False

class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ruta = Column(String, unique=True)
    
    fecha_subida = Column(DateTime, default=datetime.utcnow) 

    prediccion = Column(String, nullable=True)
    confianza = Column(Float, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="imagenes")

class HistorialChat(Base):
    __tablename__ = "historial_chat"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    mensaje_usuario = Column(Text)
    respuesta_agente = Column(Text) 
    fecha = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="historial")