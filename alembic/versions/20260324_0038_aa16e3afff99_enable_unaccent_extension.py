"""enable_unaccent_extension

Revision ID: aa16e3afff99
Revises: 245026308d91
Create Date: 2026-03-24 00:38:37.387493

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa16e3afff99"
down_revision: Union[str, None] = "245026308d91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF NOT EXISTS unaccent")
