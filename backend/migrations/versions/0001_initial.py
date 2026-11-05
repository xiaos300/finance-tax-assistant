"""Initial PostgreSQL 18 schema; snapshot SQL is frozen alongside this revision."""
from pathlib import Path
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Do not import evolving model metadata into historical migrations.
    sql = Path(__file__).with_suffix('.sql').read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise RuntimeError('No destructive downgrade; use guarded test reset or reviewed recovery.')
