from sqlalchemy import select
from app.infrastructure.database import models as m
from app.core.contracts import Rule


class KnowledgeRepository:
    def __init__(self,session):self.session=session

    def candidates(self,company,topic):
        r,rc=m.rules,m.rule_companies
        rows=self.session.execute(select(r).join(rc,(r.c.rule_id==rc.c.rule_id)&(r.c.version==rc.c.version))
            .where(rc.c.company_id==company,r.c.topic==topic,r.c.status=='enabled').order_by(r.c.rule_id,r.c.version)).mappings()
        result=[]
        for row in rows:
            data=dict(row)
            companies=list(self.session.scalars(select(rc.c.company_id).where(rc.c.rule_id==data['rule_id'],rc.c.version==data['version']).order_by(rc.c.company_id)))
            result.append(Rule(**{k:v for k,v in data.items() if k not in ('policy_json','content_hash','updated_at','effective_from')},
                policy=data['policy_json'],company_ids=companies,effective_from=data['effective_from'].isoformat()))
        return result
