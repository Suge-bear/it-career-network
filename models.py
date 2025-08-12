from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)   # store hashed password
    role = Column(String, nullable=True)
    training = relationship("Training", back_populates="user", cascade="all, delete-orphan")

class Training(Base):
    __tablename__ = "training"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="training")

class CareerPath(Base):
    __tablename__ = "career_paths"
    id = Column(String, primary_key=True)   # e.g. "sysadmin"
    title = Column(String, nullable=False)
    requirements = Column(Text, nullable=True)  # comma-separated list
