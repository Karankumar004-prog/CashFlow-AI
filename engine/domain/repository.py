from typing import List, Optional
from sqlalchemy.orm import Session
from engine.domain.models import Account, Transaction
from engine.db.database import get_db

class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Accounts ---
    def create_account(self, name: str, account_type: str, balance: float = 0.0) -> Account:
        account = Account(name=name, account_type=account_type, balance=balance)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account_by_name(self, name: str) -> Optional[Account]:
        return self.db.query(Account).filter(Account.name == name).first()

    def get_all_accounts(self) -> List[Account]:
        return self.db.query(Account).all()

    def update_account_balance(self, account_id: int, new_balance: float) -> Account:
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if account:
            account.balance = new_balance
            self.db.commit()
            self.db.refresh(account)
        return account

    # --- Transactions ---
    def add_transaction(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def add_transactions(self, transactions: List[Transaction]):
        self.db.add_all(transactions)
        self.db.commit()

    def get_all_transactions(self) -> List[Transaction]:
        return self.db.query(Transaction).all()

    def get_unclassified_transactions(self) -> List[Transaction]:
        return self.db.query(Transaction).filter(
            Transaction.classification_method == 'unclassified'
        ).all()

    def update_transaction(self, transaction: Transaction):
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def clear_all(self):
        """DANGEROUS: Clears all data from the database. Useful for resetting."""
        self.db.query(Transaction).delete()
        self.db.query(Account).delete()
        self.db.commit()
