from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)

    training = relationship("Training", back_populates="user")

class Training(Base):
    __tablename__ = "training"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    progress = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="training")

class CareerPath(Base):
    __tablename__ = "career_paths"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    requirements = Column(String(500), nullable=True)
