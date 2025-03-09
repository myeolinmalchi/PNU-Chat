"""데이터베이스 초기화 스크립트

Usage:
    $ poetry run python3 scripts/init_db.py
"""

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from db.common import Base, get_engine
from db.models import *


def init_database():
    raise Exception("DB 마이그레이션은 alembic을 사용하세요.")
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("CREATE EXTENSION vector;"))
            conn.commit()

        Base.metadata.create_all(engine)
    except ProgrammingError as e:
        print(f"Error has been occurred: {e}")
    """


if __name__ == "__main__":
    init_database()
