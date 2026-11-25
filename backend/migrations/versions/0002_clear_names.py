"""Nombres sin abreviaturas: latency_ms -> latency_milliseconds y cgpa -> grade_point_average.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25 12:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rename_input_key(old: str, new: str) -> None:
    """Renombra una clave dentro del JSON de entrada guardado en el historial."""
    op.execute(
        sa.text(
            """
            UPDATE predictions
            SET input_features = (input_features - :old)
                || jsonb_build_object(:new, input_features -> :old)
            WHERE input_features ? :old
            """
        ).bindparams(old=old, new=new)
    )


def upgrade() -> None:
    op.alter_column("predictions", "latency_ms", new_column_name="latency_milliseconds")
    _rename_input_key("cgpa", "grade_point_average")


def downgrade() -> None:
    _rename_input_key("grade_point_average", "cgpa")
    op.alter_column("predictions", "latency_milliseconds", new_column_name="latency_ms")
