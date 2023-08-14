import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped

Base = declarative_base()

class Person(Base):
    __tablename__ = "people"
    ssn = Column("ssn", Integer, primary_key=True)
    firstname = Column("firstname", String)
    lastname = Column("lastname", String)
    gender = Column("gender", CHAR)
    age = Column("age", Integer)

    def __init__(self, ssn, firstname, lastname, gender, age):
        self.ssn=ssn
        self.firstname=firstname
        self.lastname = lastname
        self.gender = gender
        self.age = age

class Thing(Base):
    __tablename__ = "things"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    description = Column("description", String)
    owner = Column(Integer, ForeignKey("people.ssn"))

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

person = Person(1234567, "Max", "Mustermann", "m", "29")
thing = Thing("test", 1234567)
session.add(person)
session.add(thing)
session.commit()
session.close()