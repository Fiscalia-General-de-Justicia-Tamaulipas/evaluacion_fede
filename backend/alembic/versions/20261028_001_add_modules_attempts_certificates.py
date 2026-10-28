"""Add modules, attempts and certificates.

Revision ID: 20261028_001
Revises: None
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "module_id" not in {c["name"] for c in inspector.get_columns("questions")}:
        op.add_column("questions", sa.Column("module_id", sa.Integer(), nullable=False, server_default="1"))
    else:
        op.alter_column("questions", "module_id", server_default="1")

    if "module_id" not in {c["name"] for c in inspector.get_columns("evaluations")}:
        op.add_column("evaluations", sa.Column("module_id", sa.Integer(), nullable=False, server_default="1"))
    if "attempt_number" not in {c["name"] for c in inspector.get_columns("evaluations")}:
        op.add_column("evaluations", sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))

    existing_unique_constraints = {
        tuple(constraint["column_names"] or [])
        for constraint in inspector.get_unique_constraints("questions")
    }
    if ("number",) in existing_unique_constraints:
        op.drop_constraint(
            next(
                constraint["name"]
                for constraint in inspector.get_unique_constraints("questions")
                if tuple(constraint["column_names"] or []) == ("number",)
            ),
            "questions",
            type_="unique",
        )

    op.create_unique_constraint(
        "uq_question_module_number",
        "questions",
        ["module_id", "number"],
    )

    if "certificates" not in inspector.get_table_names():
        op.create_table(
            "certificates",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("module_id", sa.Integer(), nullable=False),
            sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("evaluations.id"), nullable=False, unique=True),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("user_id", "module_id", name="uq_certificate_user_module"),
        )

    op.execute("ALTER TABLE questions MODIFY COLUMN module_id INT NOT NULL")
    op.execute("ALTER TABLE evaluations MODIFY COLUMN module_id INT NOT NULL")
    op.execute("ALTER TABLE evaluations MODIFY COLUMN attempt_number INT NOT NULL")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "certificates" in inspector.get_table_names():
        op.drop_table("certificates")
    op.drop_constraint("uq_question_module_number", "questions", type_="unique")
    op.drop_column("evaluations", "attempt_number")
    op.drop_column("evaluations", "module_id")
    op.drop_column("questions", "module_id")
