from abc import ABC, abstractmethod
from typing import List
from engine.domain.models import Transaction
from sqlalchemy.orm import Session

class IngestionStrategy(ABC):
    @abstractmethod
    def ingest(self, file_path: str, account_id: int, db: Session) -> List[Transaction]:
        """
        Reads data from file_path, parses it into Transaction models,
        associates them with the given account_id, and returns them.
        Does NOT commit to the DB; the caller decides when to save.
        """
        pass
