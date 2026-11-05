from alembic import context
from app.infrastructure.database.models import metadata

# Only the guarded maintenance command supplies a live Connection. No DSN in ini.
connection = context.config.attributes.get('connection')
if connection is None:
    raise RuntimeError('Use the guarded maintenance CLI; no implicit database connection.')
context.configure(connection=connection, target_metadata=metadata,
                  version_table_schema='harness', include_schemas=True)
with context.begin_transaction():
    context.run_migrations()
