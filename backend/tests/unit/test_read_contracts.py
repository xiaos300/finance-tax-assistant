"""D1 DTO/transport contracts only; these tests provide no PostgreSQL acceptance."""
import json
from pathlib import Path
from datetime import datetime,timezone
from pydantic import ValidationError
from jsonschema import Draft202012Validator,FormatChecker
import pytest
from app.core.contracts import (Principal,Invoice,InvoicePage,BankPage,BankTransaction,Totals,Metric,Check,
                               Rule,RuleResolution,RuleRef,InvoiceSearchItem)
from app.core.pagination import encode,decode
from app.core.exceptions import BusinessError
from app.modules.knowledge.policies import resolve

ROOT=Path(__file__).resolve().parents[3]
SCHEMA=json.loads((ROOT/'docs/architecture/contracts/contracts.schema.json').read_text(encoding='utf-8'))


def rule(**overrides):
    data=dict(rule_id='R002',version='2.0',name='单位测试规则',revision=1,topic='purpose',company_ids=['C001'],effective_from='2026-09-01',status='enabled',body='全部必填',policy={'kind':'all'},source_ref='synthetic fixture')
    data.update(overrides);return Rule(**data)


def test_D1_DTOs_against_unchanged_machine_contract():
    item=dict(company_id='C001',company_name='测试企业',invoice_id='UNIT',invoice_date='2026-09-01',seller='测试销售方',item_name='测试项目',amount='800.00',row_version=1)
    invoice=Invoice(**item,purpose=None,note=None,updated_at='2026-11-04T00:00:00Z')
    ref=RuleRef(rule_id='R002',version='2.0',name='单位测试规则',revision=1)
    cases=[Principal(user_id='U001',name='测试用户',companies=[dict(company_id='C001',name='测试企业',can_write=True)]),
        invoice,InvoicePage(items=[InvoiceSearchItem(**item)],next_cursor=None),
        BankPage(items=[BankTransaction(company_id='C001',transaction_id='UNIT',transaction_date='2026-09-01',direction='expense',amount='1.00',counterparty='测试',note=None)],next_cursor=None),
        Totals(company_id='C001',business_month='2026-09',currency='CNY',invoice_total=Metric(amount='800.00',record_count=1,empty=False),basis_status='resolved',rule_refs=[ref]),
        Check(company_id='C001',business_month='2026-09',queried_at='2026-11-04T00:00:00Z',rule_refs=[ref],check_status='checked',missing=[],count=0),
        RuleResolution(resolution_status='resolved',rules=[rule()],rule_refs=[ref])]
    for obj in cases:
        validator=Draft202012Validator({'$ref':'#/$defs/'+type(obj).__name__,'$defs':SCHEMA['$defs']},format_checker=FormatChecker())
        validator.validate(obj.model_dump(mode='json',exclude_unset=isinstance(obj,Totals)))


@pytest.mark.parametrize('changes',[{'effective_from':'2026-02-30'},{'company_ids':['C001','C001']},{'policy':{'kind':'unknown'}},{'policy':{'kind':'amount_gte','threshold_cents':True}},{'policy':{'kind':'all','threshold_cents':1}},{'revision':True},{'extra':1}])
def test_D1_rule_DTO_rejects_invalid(changes):
    with pytest.raises(ValidationError):rule(**changes)


def test_TC027_resolution_boundaries_without_SQL():
    assert resolve([], '2026-09','purpose').resolution_status=='missing'
    assert resolve([rule()], '2026-09','purpose').resolution_status=='resolved'
    assert resolve([rule(),rule(version='3.0')], '2026-09','purpose').resolution_status=='conflict'
    assert resolve([rule(effective_from='2026-09-15')], '2026-09','purpose').resolution_status=='unsupported'
    assert resolve([rule()], '2026-08','purpose').resolution_status=='unsupported'


def test_D1_cursor_bound_to_identity_resource_and_filters():
    filters={'company_id':'C001','q':'测试'}
    cursor=encode('invoices',filters,'U001',['C001','F001'])
    assert decode(cursor,'invoices',filters,'U001')==['C001','F001']
    for resource,f,user in [('bank',filters,'U001'),('invoices',{},'U001'),('invoices',filters,'U002')]:
        with pytest.raises(BusinessError):decode(cursor,resource,f,user)
    for invalid in ('bad','a'*2001):
        with pytest.raises(BusinessError):decode(invalid,'invoices',filters,'U001')
