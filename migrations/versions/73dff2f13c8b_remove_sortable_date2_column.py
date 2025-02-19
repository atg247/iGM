"""Remove sortable_date2 column

Revision ID: 73dff2f13c8b
Revises: 3873a6c777d9
Create Date: 2025-02-19 17:23:44.933359

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector



# revision identifiers, used by Alembic.
revision = '73dff2f13c8b'
down_revision = '3873a6c777d9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [column['name'] for column in inspector.get_columns('tgames')]

    if 'sortable_date2' in columns:
        with op.batch_alter_table('tgames', schema=None) as batch_op:
            batch_op.drop_column('sortable_date2')



def downgrade():
    with op.batch_alter_table('tgames', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sortable_date2', sa.String(length=150), nullable=True))
