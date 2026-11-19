"""Add INEGI geographic codes to municipalities.

Revision ID: 20261119_004
Revises: 20261119_003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_004"
down_revision: Union[str, Sequence[str], None] = "20261119_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "municipalities" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("municipalities")}
    if "code" not in columns:
        op.add_column(
            "municipalities",
            sa.Column("code", sa.String(length=5), nullable=True),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("municipalities")}
    if "ix_municipalities_state_id" not in indexes:
        op.create_index(
            "ix_municipalities_state_id",
            "municipalities",
            ["state_id"],
        )

    constraints = sa.inspect(bind).get_unique_constraints("municipalities")
    for constraint in constraints:
        if tuple(constraint["column_names"] or []) == ("state_id", "name"):
            op.drop_constraint(
                constraint["name"],
                "municipalities",
                type_="unique",
            )

    unique_constraints = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("municipalities")
    }
    if "uq_municipality_code" not in unique_constraints:
        op.create_unique_constraint(
            "uq_municipality_code",
            "municipalities",
            ["code"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "municipalities" not in inspector.get_table_names():
        return

    municipality = sa.table(
        "municipalities",
        sa.column("state_id", sa.Integer),
        sa.column("name", sa.String),
    )
    duplicate_name = bind.execute(
        sa.select(
            municipality.c.state_id,
            municipality.c.name,
        )
        .group_by(
            municipality.c.state_id,
            municipality.c.name,
        )
        .having(sa.func.count() > 1)
        .limit(1)
    ).first()
    if duplicate_name:
        raise RuntimeError(
            "Cannot restore unique state/name municipality names while duplicate INEGI names exist."
        )

    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("municipalities")
    }
    if "uq_municipality_code" in unique_constraints:
        op.drop_constraint(
            "uq_municipality_code",
            "municipalities",
            type_="unique",
        )

    unique_constraints = {
        tuple(constraint["column_names"] or [])
        for constraint in sa.inspect(bind).get_unique_constraints("municipalities")
    }
    if ("state_id", "name") not in unique_constraints:
        op.create_unique_constraint(
            "uq_municipality_state_name",
            "municipalities",
            ["state_id", "name"],
        )

    columns = {column["name"] for column in sa.inspect(bind).get_columns("municipalities")}
    if "code" in columns:
        op.drop_column("municipalities", "code")
