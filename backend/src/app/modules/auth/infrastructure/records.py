import uuid

from sqlalchemy import Boolean, String, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.auth.domain.role import Role
from app.shared.database import Base, CreatedAtMixin, enum_check


class AdminUserRecord(CreatedAtMixin, Base):
    __tablename__ = "admin_users"
    __table_args__ = (enum_check("role", Role, "role_allowed"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
