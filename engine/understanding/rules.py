from typing import List
import re
from engine.domain.models import Transaction

class TransactionCategorizer:
    def __init__(self, user_overrides: dict = None):
        self.user_overrides = user_overrides or {}

    def categorize_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        for tx in transactions:
            if tx.classification_method != "unclassified" and tx.classification_method != "":
                continue # Already classified
                
            # 1. User overrides (Highest priority)
            override = self.user_overrides.get(tx.raw_description)
            if override:
                tx.clean_merchant = override.get("clean_merchant", "Unknown")
                tx.transaction_type = override.get("transaction_type", "Unknown")
                tx.category = override.get("category", "Uncategorized")
                tx.sub_category = override.get("sub_category", "Uncategorized")
                tx.classification_method = "memory"
                tx.confidence_score = 1.0
                continue
                
            # 2. Basic rules (Fallback)
            desc_lower = tx.raw_description.lower()
            
            # Simple exact match/substring logic (This would be much larger in a real engine)
            if "starbucks" in desc_lower:
                tx.clean_merchant = "Starbucks"
                tx.transaction_type = "Expense"
                tx.category = "Wants"
                tx.sub_category = "Coffee/Dining"
                tx.classification_method = "rules"
                tx.confidence_score = 0.9
            elif "netflix" in desc_lower:
                tx.clean_merchant = "Netflix"
                tx.transaction_type = "Expense"
                tx.category = "Wants"
                tx.sub_category = "Subscriptions"
                tx.classification_method = "rules"
                tx.confidence_score = 0.9
            elif "payroll" in desc_lower or "salary" in desc_lower:
                tx.clean_merchant = "Employer"
                tx.transaction_type = "Income"
                tx.category = "Income"
                tx.sub_category = "Salary"
                tx.classification_method = "rules"
                tx.confidence_score = 0.9
            elif "transfer" in desc_lower or tx.amount > 0 and "zelle" in desc_lower:
                 tx.clean_merchant = "Transfer"
                 tx.transaction_type = "Transfer"
                 tx.category = "Transfers"
                 tx.sub_category = "Internal Transfer"
                 tx.classification_method = "rules"
                 tx.confidence_score = 0.8
            else:
                # Keep unclassified
                tx.clean_merchant = "Unknown"
                tx.transaction_type = "Income" if tx.amount > 0 else "Expense"
                tx.category = "Uncategorized"
                tx.sub_category = "Uncategorized"
                tx.classification_method = "unclassified"
                tx.confidence_score = 0.0
                
        return transactions
