"""TC052: exact PostgreSQL host identity, no database/network I/O."""
import json

import pytest

from app.infrastructure.database.targets import (
    Target, TargetError, canonical_server_address, instance_matches,
    parse_target, verify_authenticated,
)
from app.infrastructure.database import bootstrap, maintenance


@pytest.mark.parametrize('observed,expected',[
    ('127.0.0.1/32','127.0.0.1'),('127.0.0.1','127.0.0.1'),
    ('::1/128','::1'),('0:0:0:0:0:0:0:1/128','::1'),
    ('0:0:0:0:0:0:0:1','::1'),
])
def test_TC052_host_identity_accepts_equivalent_notations(observed,expected):
    assert canonical_server_address(observed)==expected
    assert instance_matches(observed,5432,expected,5432)
    assert instance_matches(expected,5432,observed,5432)


@pytest.mark.parametrize('observed',[
    None,'','localhost','127.1','127.0.0.1/24','127.0.0.1/0',
    '127.0.0.1/255.255.255.0','::1/64','::1%lo','127.0.0.1,127.0.0.2',
])
def test_TC052_host_identity_rejects_invalid_or_network_targets(observed):
    with pytest.raises(TargetError):canonical_server_address(observed)
    assert not instance_matches(observed,5432,'127.0.0.1',5432)


@pytest.mark.parametrize('observed,port,expected,expected_port',[
    ('127.0.0.2/32',5432,'127.0.0.1',5432),
    ('::1/128',5432,'127.0.0.1',5432),
    ('::ffff:127.0.0.1/128',5432,'127.0.0.1',5432),
    ('127.0.0.1/32',5433,'127.0.0.1',5432),
    ('127.0.0.1/32',True,'127.0.0.1',5432),
    ('127.0.0.1/32',5432,'127.0.0.1','5432'),
])
def test_TC052_normalization_does_not_expand_instance_authority(observed,port,expected,expected_port):
    assert not instance_matches(observed,port,expected,expected_port)


@pytest.mark.parametrize('address',['127.0.0.1/32','0:0:0:0:0:0:0:1/128'])
@pytest.mark.parametrize('invalid_field',[None,'database','role','superuser','schema_owner'])
def test_TC052_authenticated_mask_format_preserves_all_other_guards(address,invalid_field):
    host='127.0.0.1' if address.startswith('127') else '::1'
    row=['finance_tax_test','finance_tax_app','finance_tax_app',180006,address,5432,
         False,False,False,False,False,False,'finance_tax_migrator','UTF8','finance_tax_migrator']
    if invalid_field=='database':row[0]='tax_db'
    elif invalid_field=='role':row[2]='postgres'
    elif invalid_field=='superuser':row[6]=True
    elif invalid_field=='schema_owner':row[14]=None
    class Cursor:
        def execute(self,sql):assert sql.lstrip().startswith('SELECT')
        def fetchone(self):return tuple(row)
    target=Target(host,5432,'finance_tax_test','finance_tax_app')
    if invalid_field is None:verify_authenticated(Cursor(),target)
    else:
        with pytest.raises(TargetError):verify_authenticated(Cursor(),target)


def test_TC052_configured_ipv6_is_canonical_without_enabling_hostaddr_query():
    _,target=parse_target('postgresql+psycopg://finance_tax_app@[0:0:0:0:0:0:0:1]:5432/finance_tax_test',maintenance=False,testing=True)
    assert target.host=='::1'
    with pytest.raises(TargetError):
        parse_target('postgresql+psycopg://finance_tax_app@[::1]:5432/finance_tax_test?hostaddr=127.0.0.1',maintenance=False,testing=True)


@pytest.mark.parametrize('address,port,superuser,accepted',[
    ('127.0.0.1/32',5432,True,True),('127.0.0.2/32',5432,True,False),
    ('127.0.0.1/24',5432,True,False),('127.0.0.1/32',5433,True,False),
    ('127.0.0.1/32',5432,False,False),
])
def test_TC052_admin_inspection_uses_exact_normalized_address(monkeypatch,address,port,superuser,accepted):
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def transaction(self):return self
        def execute(self,sql):
            assert sql.startswith(('SELECT','SET TRANSACTION READ ONLY'))
            self.sql=sql
            return self
        def fetchone(self):
            if 'system_identifier' in self.sql:return ('123',)
            return ('postgres','postgres','postgres',180006,address,port,superuser)
        def fetchall(self):return []
    monkeypatch.setattr(bootstrap,'admin_connect',lambda values:Connection())
    values={'admin_database_url':'postgresql+psycopg://postgres@127.0.0.1:5432/postgres'}
    if accepted:assert bootstrap.inspect_admin(values)['identity'][4]==address
    else:
        with pytest.raises(TargetError):bootstrap.inspect_admin(values)


@pytest.mark.parametrize('receipt_ip,actual_ip,actual_port,accepted',[
    ('127.0.0.1','127.0.0.1/32',5432,True),('127.0.0.1/32','127.0.0.1',5432,True),
    ('::1','0:0:0:0:0:0:0:1/128',5432,True),
    ('127.0.0.1/32','127.0.0.2/32',5432,False),
    ('127.0.0.1/24','127.0.0.1/32',5432,False),
    ('127.0.0.1/32','127.0.0.1/32',5433,False),
])
def test_TC052_creation_provenance_keeps_instance_binding(monkeypatch,tmp_path,receipt_ip,actual_ip,actual_port,accepted):
    roles={'finance_tax_app':'200','finance_tax_migrator':'201'}
    receipt=tmp_path/'receipt.json'
    receipt.write_text(json.dumps({'database_oids':{'finance_tax_test':'100'},'role_oids':roles,
        'identity':['postgres','postgres','postgres',180006,receipt_ip,5432,True]}),encoding='utf-8')
    monkeypatch.setattr(bootstrap,'RECEIPT',receipt)
    class Connection:
        def execute(self,statement):
            assert str(statement).startswith('SELECT')
            return self
        def one(self):return ('finance_tax_test','100',actual_ip,actual_port)
        def all(self):return list(roles.items())
    if accepted:maintenance.verify_provenance(Connection())
    else:
        with pytest.raises(TargetError):maintenance.verify_provenance(Connection())
