"""fix team unique and add stat_group_name

Revision ID: e904c01f7a3c
Revises: e1db518314db
Create Date: 2025-08-29 21:48:50.792855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e904c01f7a3c'
down_revision = 'e1db518314db'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name  # 'sqlite' tai 'postgresql'
    insp = sa.inspect(bind)

    # 1) Pudota UNIQUE(team_id) vain Postgresissa (devissä sitä ei ole)
    if dialect == 'postgresql':
        op.execute(sa.text('ALTER TABLE team DROP CONSTRAINT IF EXISTS team_team_id_key'))

    # 2) Lisää tgames.stat_group_name vain jos sitä ei ole
    tgames_cols = [c['name'] for c in insp.get_columns('tgames')]
    if 'stat_group_name' not in tgames_cols:
        with op.batch_alter_table('tgames') as batch_op:
            batch_op.add_column(
                sa.Column('stat_group_name', sa.String(length=50), nullable=False, server_default='unknown')
            )

def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    insp = sa.inspect(bind)

    # Poista sarake, jos se on olemassa
    tgames_cols = [c['name'] for c in insp.get_columns('tgames')]
    if 'stat_group_name' in tgames_cols:
        with op.batch_alter_table('tgames') as batch_op:
            batch_op.drop_column('stat_group_name')

    # Palauta UNIQUE(team_id) vain Postgresissa
    if dialect == 'postgresql':
        op.execute(sa.text('ALTER TABLE team ADD CONSTRAINT team_team_id_key UNIQUE (team_id)'))