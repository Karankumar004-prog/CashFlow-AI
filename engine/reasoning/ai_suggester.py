from typing import List, Dict
from engine.domain.models import Transaction
import json

class AISuggester:
    """
    AI acts as an enhancement. It does not commit to the ledger.
    It proposes mappings for unclassified transactions.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def suggest_categorizations(self, transactions: List[Transaction]) -> Dict[str, dict]:
        """
        Takes unclassified transactions and returns suggested mappings.
        Returns a dict mapping raw_description to suggestions.
        """
        if not self.api_key or self.api_key == "mock":
            return {}
            
        unclassified = [tx for tx in transactions if tx.classification_method == "unclassified"]
        if not unclassified:
            return {}
            
        # Here we would call the actual Gemini API
        # from skills.transaction_understanding.ai import batch_classify_transactions
        # But we decouple it from the Streamlit UI state
        
        # For the engine implementation, we'll wrap the existing function if available
        # to preserve functionality, but enforce the boundary.
        try:
            from skills.transaction_understanding.ai import batch_classify_transactions
            
            # Format for the existing function
            to_classify = [
                {
                    "description": tx.raw_description,
                    "amount": tx.amount,
                    "csv_type": "",
                    "csv_category": ""
                } for tx in unclassified
            ]
            
            # This returns a dict {raw_desc: {clean_merchant, transaction_type, category, ...}}
            suggestions = batch_classify_transactions(to_classify, self.api_key)
            return suggestions
            
        except ImportError:
            return {}
