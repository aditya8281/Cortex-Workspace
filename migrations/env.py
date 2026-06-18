from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve the database URL using the same path as the app (bootstrap.py).
# This ensures CLI `alembic` commands and the running app always target
# the same SQLite file, regardless of CWD.
try:
    from backend.app.core.system_paths import ensure_system_dirs
    from backend.app.core.storage_abstraction import get_system_storage

    ensure_system_dirs()
    _db_path = str(get_system_storage().database_path)
    config.set_main_option("sqlalchemy.url", f"sqlite:///{_db_path}")
except Exception:
    # Fallback: use the URL from alembic.ini (works when bootstrap.py
    # overrides it at runtime).
    pass

# add your model's MetaData object here
# for 'autogenerate' support
from backend.app.db.base import Base  # noqa: E402
from backend.app.models.user import User  # noqa: F401, E402
from backend.app.models.auth_event import AuthEvent  # noqa: F401, E402
from backend.app.models.storage_registry import StorageRegistry  # noqa: F401, E402
from backend.app.intelligence.models import KnowledgeEntry  # noqa: F401, E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
