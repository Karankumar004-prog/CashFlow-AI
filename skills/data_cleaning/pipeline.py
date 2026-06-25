from typing import List
from skills.core.models import RawTransaction

def clean_transactions(raw_transactions: List[RawTransaction]) -> List[RawTransaction]:
    """
    Cleans raw transactions by:
    1. Standardizing dates (already done in parsing)
    2. Removing identical duplicate transactions
    """
    seen = set()
    cleaned = []
    
    for tx in raw_transactions:
        # Create a signature for deduplication
        # A transaction is duplicate if it has the exact same date, amount, and raw_description
        sig = (tx.date, tx.amount, tx.raw_description.lower().strip())
        
        if sig not in seen:
            seen.add(sig)
            cleaned.append(tx)
            
    return cleaned
