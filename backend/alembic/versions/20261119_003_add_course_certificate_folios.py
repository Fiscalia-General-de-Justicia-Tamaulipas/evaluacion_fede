"""Store one verifiable certificate per completed course.

Revision ID: 20261119_003
Revises: 20261028_002
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_003"
down_revision: Union[str, Sequence[str], None] = "20261028_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "certificates" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("certificates")}
    if "course_key" not in columns:
        op.add_column("certificates", sa.Column("course_key", sa.String(100), nullable=True))
    if "folio" not in columns:
        op.add_column("certificates", sa.Column("folio", sa.String(48), nullable=True))
    if "user_name" not in columns:
        op.add_column("certificates", sa.Column("user_name", sa.String(320), nullable=True))

    certificate_rows = sa.table(
        "certificates",
        sa.column("id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("module_id", sa.Integer),
    )
    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("first_name", sa.String()),
        sa.column("paternal_surname", sa.String()),
        sa.column("maternal_surname", sa.String()),
    )
    rows = bind.execute(
        sa.select(
            certificate_rows.c.id,
            certificate_rows.c.user_id,
            certificate_rows.c.module_id,
            users.c.first_name,
            users.c.paternal_surname,
            users.c.maternal_surname,
        ).select_from(
            certificate_rows.outerjoin(users, users.c.id == certificate_rows.c.user_id)
        )
    ).mappings()
    for row in rows:
        user_name = " ".join(
            part for part in (
                row["first_name"],
                row["paternal_surname"],
                row["maternal_surname"],
            ) if part
        ).strip()
        bind.execute(
            certificate_rows.update()
            .where(certificate_rows.c.id == row["id"])
            .values(
                course_key=f"legacy-module-{row['module_id'] or row['id']}",
                folio=f"FEDE-LEGACY-{uuid4().hex.upper()}",
                user_name=user_name,
            )
        )

    existing_uniques = {
        tuple(constraint["column_names"] or []): constraint["name"]
        for constraint in inspector.get_unique_constraints("certificates")
    }
    if ("user_id", "module_id") in existing_uniques:
        op.drop_constraint(existing_uniques[("user_id", "module_id")], "certificates", type_="unique")

    updated_columns = {column["name"]: column for column in sa.inspect(bind).get_columns("certificates")}
    for name in ("module_id", "evaluation_id", "score"):
        if name in updated_columns and not updated_columns[name]["nullable"]:
            op.alter_column(
                "certificates",
                name,
                existing_type=updated_columns[name]["type"],
                nullable=True,
            )
    for name in ("course_key", "folio", "user_name"):
        updated_columns = {column["name"]: column for column in sa.inspect(bind).get_columns("certificates")}
        if updated_columns[name]["nullable"]:
            op.alter_column(
                "certificates",
                name,
                existing_type=updated_columns[name]["type"],
                nullable=False,
            )

    unique_names = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("certificates")
    }
    if "uq_certificate_user_course" not in unique_names:
        op.create_unique_constraint(
            "uq_certificate_user_course",
            "certificates",
            ["user_id", "course_key"],
        )
    if "uq_certificate_folio" not in unique_names:
        op.create_unique_constraint("uq_certificate_folio", "certificates", ["folio"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "certificates" not in inspector.get_table_names():
        return

    certificate_rows = sa.table(
        "certificates",
        sa.column("module_id", sa.Integer),
        sa.column("evaluation_id", sa.Integer),
        sa.column("score", sa.Integer),
    )
    has_course_certificates = bind.execute(
        sa.select(sa.literal(1))
        .select_from(certificate_rows)
        .where(
            sa.or_(
                certificate_rows.c.module_id.is_(None),
                certificate_rows.c.evaluation_id.is_(None),
                certificate_rows.c.score.is_(None),
            )
        )
        .limit(1)
    ).first()
    if has_course_certificates:
        raise RuntimeError(
            "Cannot downgrade while course-level certificates exist; their module-level fields cannot be restored."
        )

    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("certificates")
    }
    for name in ("uq_certificate_folio", "uq_certificate_user_course"):
        if name in unique_names:
            op.drop_constraint(name, "certificates", type_="unique")

    columns = {column["name"]: column for column in sa.inspect(bind).get_columns("certificates")}
    for name in ("module_id", "evaluation_id", "score"):
        if columns[name]["nullable"]:
            op.alter_column(
                "certificates",
                name,
                existing_type=columns[name]["type"],
                nullable=False,
            )
    unique_constraints = {
        tuple(constraint["column_names"] or [])
        for constraint in sa.inspect(bind).get_unique_constraints("certificates")
    }
    if ("user_id", "module_id") not in unique_constraints:
        op.create_unique_constraint(
            "uq_certificate_user_module",
            "certificates",
            ["user_id", "module_id"],
        )

    columns = {column["name"] for column in sa.inspect(bind).get_columns("certificates")}
    for name in ("user_name", "folio", "course_key"):
        if name in columns:
            op.drop_column("certificates", name)
