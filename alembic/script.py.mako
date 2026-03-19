"""Script template para novas migrations Alembic.
Este arquivo é usado como base ao criar novos scripts com 'alembic revision'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "${revision}"
down_revision: Union[str, None] = ${down_revision!r}
branch_labels: Union[str, Sequence[str], None] = ${branch_labels!r}
depends_on: Union[str, Sequence[str], None] = ${depends_on!r}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
