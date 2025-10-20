"""remover densidade e renomear descricao para empresa

Revision ID: fac59dbb027a
Revises: 
Create Date: 2025-09-25 09:22:58.765820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fac59dbb027a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renomear a coluna DESCRICAO para EMPRESA
    op.alter_column(
        'MERCADO_GAS',
        'DESCRICAO',
        new_column_name='EMPRESA',
        existing_type=sa.String(255),
        existing_nullable=True
    )

    # Remover a coluna DENSIDADE
    op.drop_column('MERCADO_GAS', 'DENSIDADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'MERCADO_GAS',
        'EMPRESA',
        new_column_name='DESCRICAO',
        existing_type=sa.String(255),
        existing_nullable=True
    )

    op.add_column('MERCADO_GAS', sa.Column('DENSIDADE', sa.Float(), nullable=True))
