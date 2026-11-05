from secrets import compare_digest
from app.core.exceptions import BusinessError
from app.core.config import configuration


def authenticate(authorization: str | None):
    v=configuration()
    tokens=[v.get('demo_u001_token',''),v.get('demo_u002_token','')]
    if any(len(t)<32 for t in tokens) or tokens[0]==tokens[1]:
        raise BusinessError('NOT_READY',503,'演示身份凭证尚未受控配置')
    if not authorization or not authorization.startswith('Bearer '):
        raise BusinessError('UNAUTHENTICATED',401,'请提供有效演示凭证')
    token=authorization[7:]
    for user,secret in zip(('U001','U002'),tokens):
        if compare_digest(token.encode(),secret.encode()):return user
    raise BusinessError('UNAUTHENTICATED',401,'请提供有效演示凭证')
