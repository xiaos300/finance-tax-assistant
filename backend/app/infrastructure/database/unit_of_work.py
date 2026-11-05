from contextlib import contextmanager
from dataclasses import dataclass
from sqlalchemy import text
from app.modules.ledger.repository import LedgerRepository
from app.modules.knowledge.repository import KnowledgeRepository


@dataclass(frozen=True)
class ReadTransaction:
    ledger: LedgerRepository
    knowledge: KnowledgeRepository


def read_transactions(sessions):
    @contextmanager
    def begin():
        with sessions() as session:
            with session.begin():
                session.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
                yield ReadTransaction(LedgerRepository(session),KnowledgeRepository(session))
    return begin
