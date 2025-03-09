from dotenv import load_dotenv

from alembic import context

from db.common import Base, get_engine
from db.models import *

load_dotenv()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    pass


def run_migrations_online():
    connectable = get_engine()

    with connectable.connect() as conn:
        context.configure(
            connection=conn,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
