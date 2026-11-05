from datetime import date
from app.core.contracts import RuleResolution, RuleRef


def resolve(candidates, month, topic):
    from app.modules.ledger.policies import month_bounds
    start,end=month_bounds(month)
    if topic=='purpose' and month!='2026-09':
        return RuleResolution(resolution_status='unsupported',rules=[],rule_refs=[])
    candidates=[r for r in candidates if r.status=='enabled' and (end is None or date.fromisoformat(r.effective_from)<end)]
    midmonth=any(date.fromisoformat(r.effective_from)>start for r in candidates)
    status='conflict' if len(candidates)>1 else 'unsupported' if midmonth else 'resolved' if candidates else 'missing'
    refs=[RuleRef(rule_id=r.rule_id,name=r.name,version=r.version,revision=r.revision) for r in candidates]
    return RuleResolution(resolution_status=status,rules=candidates,rule_refs=refs)
