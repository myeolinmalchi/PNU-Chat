from sqlalchemy import Engine, Integer, MetaData, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import as_declarative
from contextvars import ContextVar
from dotenv import load_dotenv

load_dotenv()

import os

N_DIM, V_DIM = (1024, 250002)

metadata = MetaData()


@as_declarative(metadata=metadata)
class Base:
    metadata: MetaData

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def __getitem__(self, key: str):
        return self.__dict__[key]

    def __setitem__(self, key: str, value):
        setattr(self, key, value)


session_context_var: ContextVar = ContextVar("db_session", default=None)

_engine = None
_Session = None

from sqlalchemy import Enum

_values_callable = lambda obj: [e.value for e in obj]
SQLEnum = lambda SomeEnum: Enum(SomeEnum, values_callable=_values_callable)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        db_type = "postgresql"
        user = os.environ.get("DB_USER")
        pw = os.environ.get("DB_PASSWORD")
        host = os.environ.get("DB_HOST")
        db_name = os.environ.get("DB_NAME")

        _engine = create_engine(f"{db_type}://{user}:{pw}@{host}/{db_name}")

    return _engine


def get_session() -> Session:
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), expire_on_commit=False)

    return _Session()


_aengine = None
_ASession = None


def get_async_engine() -> AsyncEngine:
    global _aengine
    if _aengine is None:
        db_type = "postgresql"
        user = os.environ.get("DB_USER")
        pw = os.environ.get("DB_PASSWORD")
        host = os.environ.get("DB_HOST")
        db_name = os.environ.get("DB_NAME")

        _aengine = create_async_engine(f"{db_type}://{user}:{pw}@{host}/{db_name}")

    return _aengine


def get_async_session() -> AsyncSession:
    global _ASession
    if _ASession is None:
        _ASession = async_sessionmaker(bind=get_async_engine(), expire_on_commit=False)

    return _ASession()
