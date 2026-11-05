from datetime import date, datetime, timezone
from pathlib import Path
import hashlib
import json
from sqlalchemy import select, func, text
from app.infrastructure.database import models as m

SEED = Path(__file__).resolve().parents[4]/'data/seed'


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def load_bundle(directory=SEED):
    business,rules,manifest=[json.loads((directory/f'{name}.json').read_text(encoding='utf-8')) for name in ('business','rules','manifest')]
    digest=hashlib.sha256(canonical([business,rules]).encode()).hexdigest()
    if digest!=manifest['normalized_hash'] or business['dataset_id']!=rules['dataset_id'] or business['dataset_id']!=manifest['dataset_id']:
        raise ValueError('Seed bundle hash or dataset mismatch')
    root=SEED.parents[1]
    for name,digest in manifest['source_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Protected source hash mismatch')
    return business,rules,manifest


def validate_existing(connection,business,rules):
    for key,table,ids in [('companies',m.companies,['company_id']),('users',m.users,['user_id']),('permissions',m.permissions,['user_id','company_id']),('invoices',m.invoices,['company_id','invoice_id']),('bank_transactions',m.bank_transactions,['company_id','transaction_id'])]:
        actual={tuple(row) for row in connection.execute(select(*(table.c[k] for k in ids)))}
        if not {tuple(r[k] for k in ids) for r in business[key]}<=actual:raise ValueError('Seed keys missing')
    actual=set(connection.execute(select(m.rules.c.rule_id,m.rules.c.version)).all())
    if not {(r['rule_id'],r['version']) for r in rules['rules']}<=actual:raise ValueError('Seed rule keys missing')


def seed(connection, directory=SEED):
    from app.infrastructure.database.maintenance import verify_provenance
    verify_provenance(connection)
    business,rules,manifest=load_bundle(directory)
    connection.execute(text('SELECT pg_catalog.pg_advisory_xact_lock(20261101,1)'))
    existing=connection.execute(select(m.seed_meta)).mappings().all()
    if existing:
        if len(existing)!=1 or any(existing[0][k]!=manifest[v] for k,v in [('dataset_id','dataset_id'),('normalized_hash','normalized_hash'),('schema_revision','schema_revision'),('source_hashes_json','source_hashes')]):
            raise ValueError('Existing seed metadata differs; refusing overwrite')
        # Validate original keys, not original mutable purpose/note values.
        validate_existing(connection,business,rules)
        return 'verified_existing'
    for table in m.metadata.sorted_tables:
        if connection.scalar(select(func.count()).select_from(table)):
            raise ValueError('Partial or populated database without seed marker; refusing overwrite')
    now=datetime.now(timezone.utc)
    for key,table in [('companies',m.companies),('users',m.users),('permissions',m.permissions),('invoices',m.invoices),('bank_transactions',m.bank_transactions)]:
        rows=[]
        for source in business[key]:
            r={k:v for k,v in source.items() if k!='source_ref'}
            for k in ('invoice_date','transaction_date'):
                if k in r:r[k]=date.fromisoformat(r[k])
            if key=='invoices':r.update(row_version=1,updated_at=now)
            if key=='users':r['memory_revision']=0
            rows.append(r)
        connection.execute(table.insert(),rows)
    for rule in rules['rules']:
        row={k:v for k,v in rule.items() if k not in ('policy','company_ids')}
        row.update(effective_from=date.fromisoformat(row['effective_from']),policy_json=rule['policy'],revision=1,
            content_hash=hashlib.sha256(canonical(rule).encode()).hexdigest(),updated_at=now)
        connection.execute(m.rules.insert().values(**row))
        connection.execute(m.rule_companies.insert(),[dict(rule_id=row['rule_id'],version=row['version'],company_id=cid) for cid in rule['company_ids']])
    connection.execute(m.seed_meta.insert().values(dataset_id=manifest['dataset_id'],source_hashes_json=manifest['source_hashes'],normalized_hash=manifest['normalized_hash'],schema_revision='0001',loaded_at=now))
    return 'loaded'
