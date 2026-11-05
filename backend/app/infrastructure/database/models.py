"""Single SQLAlchemy table model, PostgreSQL-only types and native constraints."""
from sqlalchemy import (MetaData, Table, Column, Text, Integer, BigInteger, Boolean,
                        Date, DateTime, ForeignKeyConstraint, CheckConstraint, UniqueConstraint,
                        Index, Identity, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import registry

metadata = MetaData(schema='harness', naming_convention={
    'pk': 'pk_%(table_name)s', 'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s', 'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'ix': 'ix_%(table_name)s_%(column_0_name)s'})
mapper_registry = registry(metadata=metadata)


def col(name, typ=Text, *, null=False, pk=False, default=None):
    return Column(name, typ, nullable=null, primary_key=pk, server_default=default)


def fk(local, remote):
    return ForeignKeyConstraint(local.split(','), ['harness.' + x for x in remote.split(',')], ondelete='RESTRICT')


def ck(name, expression):
    return CheckConstraint(expression, name=name)


def table(name, *items):
    t = Table(name, metadata, *items)
    mapper_registry.map_imperatively(type(''.join(x.title() for x in name.split('_')), (), {}), t)
    return t


def stamp(name='updated_at', null=False):
    return col(name, DateTime(timezone=True), null=null)


def version(name='row_version', initial=1):
    return col(name, Integer, default=str(initial)), ck(name, f'{name}>={initial}')


def js(name, *, kind=None, null=False, default=None):
    c = col(name, JSONB, null=null, default=text(default) if default is not None else None)
    return (c, ck(name+'_shape', f"jsonb_typeof({name})='{kind}'")) if kind else (c,)


companies = table('companies', col('company_id',pk=True),col('name'),col('short_name'),UniqueConstraint('short_name'))
users = table('users',col('user_id',pk=True),col('name'),*version('memory_revision',0))
permissions = table('user_company_permissions',col('user_id',pk=True),col('company_id',pk=True),
    col('can_read',Boolean),col('can_write',Boolean),fk('user_id','users.user_id'),fk('company_id','companies.company_id'),
    ck('write_requires_read','NOT can_write OR can_read'))
invoices = table('invoices',col('company_id',pk=True),col('invoice_id',pk=True),col('invoice_date',Date),
    col('seller'),col('item_name'),col('amount_cents',BigInteger),col('purpose',null=True),col('note',null=True),
    *version(),stamp(),fk('company_id','companies.company_id'),ck('amount','amount_cents>=0'))
Index('ix_invoices_company_date',invoices.c.company_id,invoices.c.invoice_date,invoices.c.invoice_id)
bank_transactions = table('bank_transactions',col('company_id',pk=True),col('transaction_id',pk=True),
    col('transaction_date',Date),col('direction'),col('amount_cents',BigInteger),col('counterparty'),col('note',null=True),
    fk('company_id','companies.company_id'),ck('amount','amount_cents>0'),ck('direction',"direction IN ('income','expense')"))
Index('ix_bank_company_date_direction',bank_transactions.c.company_id,bank_transactions.c.transaction_date,bank_transactions.c.direction)
sessions = table('sessions',col('session_id',pk=True),col('user_id'),col('default_company_id',null=True),
    *js('result_focus_json',null=True),*version(),stamp('created_at'),stamp(),fk('user_id','users.user_id'),
    fk('default_company_id','companies.company_id'),
    fk('user_id,default_company_id','user_company_permissions.user_id,user_company_permissions.company_id'))
Index('ix_sessions_user_created',sessions.c.user_id,sessions.c.created_at,sessions.c.session_id)
turns = table('turns',col('turn_id',pk=True),col('session_id'),col('request_hash'),col('status'),
    col('cancel_requested',Boolean,default='false'),col('session_version',Integer),*js('scope_json',null=True),
    *js('scope_company_ids',kind='array',default="'[]'::jsonb"),col('memory_revision',Integer),
    *js('result_json',null=True),col('error_code',null=True),stamp('started_at'),stamp('finished_at',null=True),
    fk('session_id','sessions.session_id'),ck('session_version','session_version>=1'),ck('memory_revision','memory_revision>=0'),
    ck('status',"status IN ('running','completed','failed','interrupted','cancelled')"),
    ck('finished',"(status='running') = (finished_at IS NULL)"),ck('result',"status='running' OR result_json IS NOT NULL"))
Index('ux_turns_one_running',turns.c.session_id,unique=True,postgresql_where=text("status='running'"))
Index('ix_turns_session_started',turns.c.session_id,turns.c.started_at,turns.c.turn_id)
messages = table('messages',col('message_id',pk=True),col('turn_id'),col('role'),col('content'),
    *js('invoice_refs_json',kind='array',default="'[]'::jsonb"),*js('memory_refs_json',kind='array',default="'[]'::jsonb"),
    *js('scope_company_ids',kind='array',default="'[]'::jsonb"),stamp('created_at'),fk('turn_id','turns.turn_id'),
    UniqueConstraint('turn_id','role'),ck('role',"role IN ('user','assistant')"),
    ck('assistant_refs',"role='user' OR invoice_refs_json='[]'::jsonb"))
rules = table('rules',col('rule_id',pk=True),col('version',pk=True),col('name'),col('topic'),col('effective_from',Date),
    col('status'),col('body'),*js('policy_json',kind='object'),*version('revision'),col('source_ref'),col('content_hash'),stamp(),
    ck('topic',"topic IN ('amount','purpose','bank')"),ck('status',"status IN ('enabled','disabled')"))
Index('ix_rules_topic_status_date',rules.c.topic,rules.c.status,rules.c.effective_from)
rule_companies = table('rule_companies',col('rule_id',pk=True),col('version',pk=True),col('company_id',pk=True),
    fk('rule_id,version','rules.rule_id,rules.version'),fk('company_id','companies.company_id'))
Index('ix_rule_companies_company',rule_companies.c.company_id,rule_companies.c.rule_id,rule_companies.c.version)
tasks = table('tasks',col('task_id',pk=True),col('user_id'),col('company_id'),col('goal'),col('business_month',null=True),
    col('status'),*js('progress_json',kind='object',default="'{}'::jsonb"),*version(),col('source_turn_id'),
    *js('last_change_origin_json',kind='object'),stamp('created_at'),stamp(),fk('user_id','users.user_id'),
    fk('company_id','companies.company_id'),fk('source_turn_id','turns.turn_id'),
    ck('month',"business_month IS NULL OR business_month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$' AND left(business_month,4)<>'0000'"),
    ck('status',"status IN ('active','awaiting_input','verify_pending','completed','cancelled')"))
Index('ux_tasks_one_open',tasks.c.user_id,tasks.c.company_id,unique=True,
      postgresql_where=text("status IN ('active','awaiting_input','verify_pending')"))
Index('ix_tasks_user_company_updated',tasks.c.user_id,tasks.c.company_id,tasks.c.updated_at)
preferences = table('preferences',col('preference_id',pk=True),col('user_id'),col('company_id'),col('preference_key'),
    col('content'),col('source_turn_id'),*js('last_change_origin_json',kind='object'),*version(),stamp('created_at'),stamp(),
    fk('user_id','users.user_id'),fk('company_id','companies.company_id'),fk('source_turn_id','turns.turn_id'),
    UniqueConstraint('user_id','company_id','preference_key'))
Index('ux_preferences_one_default',preferences.c.user_id,unique=True,postgresql_where=text("preference_key='default_company'"))
write_operations = table('write_operations',col('operation_id',pk=True),col('turn_id'),col('user_id'),col('company_id'),
    col('invoice_id'),col('request_hash'),col('expected_row_version',Integer),*js('authorization_json',kind='object'),
    *js('changes_json',kind='object'),*js('before_json',kind='object'),*js('after_json',null=True),col('state'),
    col('error_code',null=True),stamp('created_at'),stamp('committed_at',null=True),stamp('verified_at',null=True),
    fk('turn_id','turns.turn_id'),fk('user_id','users.user_id'),fk('company_id,invoice_id','invoices.company_id,invoices.invoice_id'),
    UniqueConstraint('turn_id','company_id','invoice_id'),ck('version','expected_row_version>=1'),
    ck('state',"state IN ('prepared','committed','verified','already_current','failed','verify_pending')"))
Index('ix_write_operations_user_created',write_operations.c.user_id,write_operations.c.created_at)
Index('ix_write_operations_invoice_created',write_operations.c.company_id,write_operations.c.invoice_id,write_operations.c.created_at)
evidence_events = table('evidence_events',Column('event_id',BigInteger,Identity(),primary_key=True),
    col('session_id',null=True),col('turn_id',null=True),col('user_id',null=True),col('actor_label'),
    *js('scope_company_ids',kind='array',default="'[]'::jsonb"),col('kind'),col('correlation_id'),
    *js('payload_json'),col('payload_hash'),stamp('created_at'),fk('session_id','sessions.session_id'),
    fk('turn_id','turns.turn_id'),fk('user_id','users.user_id'))
Index('ix_evidence_turn',evidence_events.c.turn_id,evidence_events.c.event_id)
Index('ix_evidence_session',evidence_events.c.session_id,evidence_events.c.event_id)
Index('ix_evidence_user_created',evidence_events.c.user_id,evidence_events.c.created_at)
seed_meta = table('seed_meta',col('dataset_id',pk=True),*js('source_hashes_json',kind='object'),col('normalized_hash'),
    col('schema_revision'),stamp('loaded_at'))
