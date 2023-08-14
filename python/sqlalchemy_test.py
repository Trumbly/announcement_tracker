import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship
from typing import List, Optional
from dataclasses import dataclass

Base = declarative_base()

@dataclass
class Person(Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    firstname: Mapped[str] = mapped_column(String)
    lastname: Mapped[str] = mapped_column(String)
    gender: Mapped[chr] = mapped_column(CHAR)
    age: Mapped[int] = mapped_column(Integer)
    things: Mapped[List["Thing"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

    def __init__(self, firstname, lastname, gender, age):
        self.firstname=firstname
        self.lastname = lastname
        self.gender = gender
        self.age = age

class Thing(Base):
    __tablename__ = "things"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String)
    owner_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    owner: Mapped["Person"] = relationship(back_populates="things")

    def __init__(self, description, owner):
        self.description = description
        self.owner = owner


load_dotenv() #load environment variables from .env file

# Create a PostgreSQL database connection
POSTGRE_HOST = os.environ.get("POSTGRE_HOST")
POSTGRE_PORT = os.environ.get("POSTGRE_PORT")
POSTGRE_USER = os.environ.get("POSTGRE_USER")
POSTGRE_PASSWORD = os.environ.get("POSTGRE_PASSWORD")
engine = create_engine(f'postgresql+psycopg2://{POSTGRE_USER}:{POSTGRE_PASSWORD}@{POSTGRE_HOST}:{POSTGRE_PORT}/test', echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()


person = Person("Hannes", "ladendorf", "m", "29")
thing = Thing("python Super power book", owner=person)
session.add(person)

# session.add(thing)
session.commit()
session.close()