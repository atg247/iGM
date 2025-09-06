"""sync changes: move tgames.team_id -> FK to team.id

Revision ID: 2b47cf5bcf8e
Revises: e904c01f7a3c
Create Date: 2025-09-06 09:01:08.552166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b47cf5bcf8e'
down_revision = 'e904c01f7a3c'
branch_labels = None
depends_on = None


def upgrade():
    """
    Change tgames.team_id from String->Integer and point FK to team.id.

    Implemented with explicit table rebuild to avoid SQLite batch issues:
      1) Add temporary Integer column team_id_int and backfill via join
      2) Create new table tgames_new with desired schema (FK to team.id)
      3) Copy data from old table into new (using team_id_int)
      4) Drop old table and rename tgames_new -> tgames
      5) Create index on team_id
    """

    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) Add temporary column for integer IDs (idempotent)
    existing_cols = {c['name'] for c in insp.get_columns('tgames')}
    if 'team_id_int' not in existing_cols:
        op.add_column('tgames', sa.Column('team_id_int', sa.Integer(), nullable=True))

    # Backfill the mapping from team.team_id (String) -> team.id (Integer)
    op.execute(
        sa.text(
            """
            UPDATE tgames
            SET team_id_int = (
                SELECT id FROM team
                WHERE team.team_id = tgames.team_id
                  AND team.stat_group = tgames.stat_group_name
            )
            WHERE team_id_int IS NULL
            """
        )
    )

    # 2) Create new table with correct schema
    if 'tgames_new' not in insp.get_table_names():
        op.create_table(
            'tgames_new',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('game_id', sa.String(length=100), nullable=False),
            sa.Column('team_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.String(length=50), nullable=False),
            sa.Column('time', sa.String(length=50), nullable=False),
            sa.Column('home_team', sa.String(length=150), nullable=False),
            sa.Column('away_team', sa.String(length=150), nullable=False),
            sa.Column('home_goals', sa.String(length=50), nullable=False),
            sa.Column('away_goals', sa.String(length=50), nullable=False),
            sa.Column('location', sa.String(length=150), nullable=False),
            sa.Column('level_name', sa.String(length=150), nullable=False),
            sa.Column('stat_group_name', sa.String(length=50), nullable=False),
            sa.Column('small_area_game', sa.String(length=50), nullable=False),
            sa.Column('team_name', sa.String(length=150), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('sortable_date', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['team_id'], ['team.id'], name='fk_tgames_team_id_team', ondelete='CASCADE'),
        )

    # 3) Copy data
    op.execute(
        sa.text(
            """
            INSERT INTO tgames_new (
                id, game_id, team_id, date, time, home_team, away_team,
                home_goals, away_goals, location, level_name, stat_group_name,
                small_area_game, team_name, type, sortable_date
            )
            SELECT
                id, game_id, team_id_int, date, time, home_team, away_team,
                home_goals, away_goals, location, level_name, stat_group_name,
                small_area_game, team_name, type, sortable_date
            FROM tgames
            """
        )
    )

    # 4) Replace old table
    op.drop_table('tgames')
    op.rename_table('tgames_new', 'tgames')

    # 5) Create index
    op.create_index('ix_tgames_team_id', 'tgames', ['team_id'], unique=False)


def downgrade():
    """
    Revert to String-based team_id referencing team.team_id.
    """

    # Create old schema table
    op.create_table(
        'tgames_old',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('game_id', sa.String(length=100), nullable=False),
        sa.Column('team_id', sa.String(length=100), nullable=False),
        sa.Column('date', sa.String(length=50), nullable=False),
        sa.Column('time', sa.String(length=50), nullable=False),
        sa.Column('home_team', sa.String(length=150), nullable=False),
        sa.Column('away_team', sa.String(length=150), nullable=False),
        sa.Column('home_goals', sa.String(length=50), nullable=False),
        sa.Column('away_goals', sa.String(length=50), nullable=False),
        sa.Column('location', sa.String(length=150), nullable=False),
        sa.Column('level_name', sa.String(length=150), nullable=False),
        sa.Column('stat_group_name', sa.String(length=50), nullable=False),
        sa.Column('small_area_game', sa.String(length=50), nullable=False),
        sa.Column('team_name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('sortable_date', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['team.team_id'], name='fk_tgames_team_id_team_team_id'),
    )

    # Copy data back converting integer id -> string key
    op.execute(
        sa.text(
            """
            INSERT INTO tgames_old (
                id, game_id, team_id, date, time, home_team, away_team,
                home_goals, away_goals, location, level_name, stat_group_name,
                small_area_game, team_name, type, sortable_date
            )
            SELECT
                t.id, t.game_id, team.team_id, t.date, t.time, t.home_team, t.away_team,
                t.home_goals, t.away_goals, t.location, t.level_name, t.stat_group_name,
                t.small_area_game, t.team_name, t.type, t.sortable_date
            FROM tgames AS t
            LEFT JOIN team ON team.id = t.team_id
            """
        )
    )

    # Drop new table and rename old back
    op.drop_index('ix_tgames_team_id', table_name='tgames')
    op.drop_table('tgames')
    op.rename_table('tgames_old', 'tgames')
