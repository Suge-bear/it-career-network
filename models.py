from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)  # new field for hashed password
    role = Column(String)
    training = relationship("Training", back_populates="user")

class Training(Base):
    __tablename__ = 'training'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    progress = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="training")

class CareerPath(Base):
    __tablename__ = 'career_paths'
    id = Column(String, primary_key=True)
    title = Column(String)
    requirements = Column(Text)
