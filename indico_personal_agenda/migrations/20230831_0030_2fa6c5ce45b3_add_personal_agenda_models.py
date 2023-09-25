"""Add personal agenda models

Revision ID: 2fa6c5ce45b3
Revises:
Create Date: 2023-08-31 00:30:14.416828
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

# revision identifiers, used by Alembic.
revision = "2fa6c5ce45b3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSchema("plugin_personal_agenda"))
    op.create_table(
        "starred",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contribution_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["contribution_id"],
            ["events.contributions.id"],
            name=op.f("fk_starred_contribution_id_contributions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.users.id"], name=op.f("fk_starred_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_starred")),
        schema="plugin_personal_agenda",
    )
    op.create_index(
        op.f("ix_starred_contribution_id"),
        "starred",
        ["contribution_id"],
        unique=False,
        schema="plugin_personal_agenda",
    )


def downgrade():
    op.drop_index(
        op.f("ix_starred_contribution_id"),
        table_name="starred",
        schema="plugin_personal_agenda",
    )
    op.drop_table("starred", schema="plugin_personal_agenda")
    op.execute(DropSchema("plugin_personal_agenda"))
