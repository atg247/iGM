"""Lisätty Team taulukko ja UserTeam taulukko

Revision ID: e2cacdd0a047
Revises: 382fe878585d
Create Date: 2024-11-04 21:03:34.422968

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2cacdd0a047'
down_revision = '382fe878585d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('managed_teams')
        batch_op.drop_column('followed_teams')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('followed_teams', sa.VARCHAR(length=512), nullable=True))
        batch_op.add_column(sa.Column('managed_teams', sa.VARCHAR(length=512), nullable=True))

    # ### end Alembic commands ###
