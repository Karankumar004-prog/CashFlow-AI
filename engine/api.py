from engine.db.database import get_db, init_db
from engine.domain.repository import LedgerRepository
from engine.ingestion.csv_ingester import CSVIngester
from engine.understanding.rules import TransactionCategorizer
from engine.math.metrics import calculate_snapshot, FinancialSnapshot
from engine.reasoning.ai_suggester import AISuggester
from engine.reasoning.coach import FinancialCoach
from typing import List, Dict

class CashFlowEngine:
    """
    Main orchestration class. 
    Decouples UI (Streamlit) from Business Logic.
    """
    def __init__(self, db_session, api_key: str = "mock"):
        self.repo = LedgerRepository(db_session)
        self.categorizer = TransactionCategorizer()
        self.ai_suggester = AISuggester(api_key)
        self.coach = FinancialCoach(api_key)
        
    @staticmethod
    def initialize_database():
        init_db()

    def load_from_csv(self, file_path: str, account_name: str) -> None:
        """Ingests CSV and parses into raw transactions."""
        account = self.repo.get_account_by_name(account_name)
        if not account:
            account = self.repo.create_account(name=account_name, account_type="asset")
            
        ingester = CSVIngester()
        txs = ingester.ingest(file_path, account.id, self.repo.db)
        
        # Save raw transactions
        self.repo.add_transactions(txs)
        
    def process_unclassified_transactions(self) -> None:
        """Runs the deterministic rules engine on unclassified transactions."""
        unclassified = self.repo.get_unclassified_transactions()
        
        # Apply deterministic rules
        classified = self.categorizer.categorize_transactions(unclassified)
        
        # Commit rules
        for tx in classified:
            self.repo.update_transaction(tx)
            
    def get_ai_suggestions(self) -> Dict[str, dict]:
        """Optionally fetches AI suggestions for remaining unclassified txs."""
        unclassified = self.repo.get_unclassified_transactions()
        return self.ai_suggester.suggest_categorizations(unclassified)
        
    def apply_ai_suggestions(self, suggestions: Dict[str, dict]):
        """Commits AI suggestions to the ledger after user approval/deterministic check."""
        unclassified = self.repo.get_unclassified_transactions()
        for tx in unclassified:
            if tx.raw_description in suggestions:
                s = suggestions[tx.raw_description]
                tx.clean_merchant = s.get("clean_merchant", tx.clean_merchant)
                tx.transaction_type = s.get("transaction_type", tx.transaction_type)
                tx.category = s.get("category", tx.category)
                tx.sub_category = s.get("sub_category", tx.sub_category)
                tx.classification_method = "ai_fallback"
                tx.confidence_score = 0.8
                self.repo.update_transaction(tx)

    def get_snapshot(self) -> FinancialSnapshot:
        """Deterministic financial math."""
        accounts = self.repo.get_all_accounts()
        transactions = self.repo.get_all_transactions()
        return calculate_snapshot(accounts, transactions)
        
    def get_coach_advice(self) -> str:
        """Downstream AI Reasoning."""
        snapshot = self.get_snapshot()
        return self.coach.generate_roadmap(snapshot)
