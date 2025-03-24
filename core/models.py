from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import relationship
from fastapi_users.db import SQLAlchemyBaseUserTable
from core.database import Base

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    links = relationship("Link", back_populates="user")

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String)
    short_code = Column(String, unique=True, index=True)
    custom_alias = Column(String, unique=True, index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)

    user = relationship("User", back_populates="links")
    project = relationship("Project", back_populates="links")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    links = relationship("Link", back_populates="project") 