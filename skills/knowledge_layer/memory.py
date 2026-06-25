from datetime import date
from typing import Optional
from skills.core.models import ProcessedTransaction
from skills.transaction_understanding.rules import derive_intent_and_impact

def match_user_memory(
    clean_desc: str,
    overrides_dict: dict,
    amount: float,
    date_val: Optional[date] = None,
    raw_desc: Optional[str] = None
) -> Optional[ProcessedTransaction]:
    """
    Checks the cleaned description against a dictionary of user-defined category overrides.
    Returns a ProcessedTransaction with a confidence of 0.95 if matched, otherwise None.
    """
    actual_date = date_val or date.today()
    actual_raw = raw_desc or clean_desc
    
    if clean_desc in overrides_dict:
        override = overrides_dict[clean_desc]
        cat = override.get("category", "Other")
        subcat = override.get("sub_category", "Uncategorized")
        return ProcessedTransaction(
            date=actual_date,
            raw_description=actual_raw,
            amount=amount,
            clean_merchant=override.get("merchant_name", clean_desc),
            transaction_type=override.get("transaction_type", "Expense"),
            category=cat,
            sub_category=subcat,
            intent=derive_intent_and_impact(cat, subcat)[0],
            financial_impact=derive_intent_and_impact(cat, subcat)[1],
            confidence_score=0.95,
            classification_method="memory"
        )
        
    return None
