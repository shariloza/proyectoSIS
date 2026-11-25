"""Base declarativa de SQLAlchemy y utilidades comunes del esquema."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import URL, CheckConstraint, DateTime, MetaData, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


def create_session_factory(url: URL | str) -> sessionmaker[Session]:
    import app.records  # noqa: F401 - registra todas las tablas antes de usar la sesión

    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    return sessionmaker(engine, expire_on_commit=False)


def enum_check(column: str, enum: type[StrEnum], name: str) -> CheckConstraint:
    """CHECK que restringe una columna de texto a los valores de un enum de dominio."""
    allowed = ", ".join(f"'{member.value}'" for member in enum)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)
