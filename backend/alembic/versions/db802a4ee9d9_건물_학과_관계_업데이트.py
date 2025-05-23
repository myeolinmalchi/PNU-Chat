"""건물-학과 관계 업데이트

Revision ID: db802a4ee9d9
Revises: b2e0324c6b7c
Create Date: 2025-02-03 02:07:56.748342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db802a4ee9d9'
down_revision: Union[str, None] = 'b2e0324c6b7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('department_building_association',
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.Column('building_num', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['building_num'], ['buildings.building_num'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.PrimaryKeyConstraint('department_id', 'building_num')
    )
    op.drop_table('association')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('association',
    sa.Column('department_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('building_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], name='association_building_id_fkey'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name='association_department_id_fkey'),
    sa.PrimaryKeyConstraint('department_id', 'building_id', 'id', name='association_pkey')
    )
    op.drop_table('department_building_association')
    # ### end Alembic commands ###
