from datetime import date
from typing import Optional
from skills.core.models import RawTransaction, ProcessedTransaction
from skills.data_cleaning.cleaner import clean_transaction_description

INTENT_IMPACT_MAPPING = {
    "Food": {
        "Restaurant": ("Lifestyle", "Variable Expense"),
        "Dining": ("Lifestyle", "Variable Expense"),
        "Coffee": ("Lifestyle", "Variable Expense"),
        "Snacks": ("Lifestyle", "Variable Expense"),
        "Groceries": ("Essential", "Variable Expense")
    },
    "Shopping": {
        "Clothing": ("Lifestyle", "Variable Expense"),
        "Electronics": ("Lifestyle", "Variable Expense"),
        "Books": ("Education", "Variable Expense"),
        "General": ("Lifestyle", "Variable Expense")
    },
    "Medical": {
        "Medicine": ("Health", "Variable Expense"),
        "Pharmacy": ("Health", "Variable Expense"),
        "Consultation": ("Health", "Variable Expense"),
        "Hospital": ("Health", "Variable Expense")
    },
    "Housing": {
        "Rent": ("Essential", "Fixed Expense"),
        "Utilities": ("Essential", "Fixed Expense"),
        "Maintenance": ("Essential", "Variable Expense")
    },
    "Transport": {
        "Fuel": ("Essential", "Variable Expense"),
        "Public": ("Essential", "Variable Expense"),
        "Cab": ("Lifestyle", "Variable Expense"),
        "Flights": ("Lifestyle", "Variable Expense")
    },
    "Entertainment": {
        "Streaming": ("Lifestyle", "Fixed Expense"),
        "Games": ("Lifestyle", "Variable Expense"),
        "Movies": ("Lifestyle", "Variable Expense")
    },
    "Investment": {
        "SIP": ("Investment", "Wealth Building"),
        "Mutual Fund": ("Investment", "Wealth Building"),
        "Shares": ("Investment", "Wealth Building")
    },
    "Income": {
        "Salary": ("Essential", "Wealth Building"),
        "Interest": ("Investment", "Wealth Building"),
        "Dividend": ("Investment", "Wealth Building"),
        "Refund": ("Essential", "Cash Transfer")
    },
    "Transfer": {
        "Family": ("Family Support", "Cash Transfer"),
        "Self": ("Essential", "Cash Transfer")
    },
    "Loan/Debt": {
        "EMI": ("Debt Payment", "Liability Reduction"),
        "Credit Card": ("Debt Payment", "Liability Reduction")
    }
}

from typing import Tuple

def derive_intent_and_impact(category: str, sub_category: str) -> Tuple[str, str]:
    cat_map = INTENT_IMPACT_MAPPING.get(category, {})
    return cat_map.get(sub_category, ("Uncategorized", "Uncategorized"))

# Predefined dictionary for exact matches on cleaned descriptions
EXACT_MATCH_RULES = {
    "NETFLIX": {
        "transaction_type": "Expense",
        "category": "Entertainment",
        "sub_category": "Streaming",
        "merchant_name": "Netflix"
    },
    "SPOTIFY": {
        "transaction_type": "Expense",
        "category": "Entertainment",
        "sub_category": "Streaming",
        "merchant_name": "Spotify"
    },
    "STARBUCKS": {
        "transaction_type": "Expense",
        "category": "Food",
        "sub_category": "Coffee",
        "merchant_name": "Starbucks"
    },
    "CHRONIC TACOS": {
        "transaction_type": "Expense",
        "category": "Food",
        "sub_category": "Dining",
        "merchant_name": "Chronic Tacos"
    },
    "RENT": {
        "transaction_type": "Expense",
        "category": "Housing",
        "sub_category": "Rent",
        "merchant_name": "Rent"
    },
    "LANDLORD RENT": {
        "transaction_type": "Expense",
        "category": "Housing",
        "sub_category": "Rent",
        "merchant_name": "Rent"
    }
}

def match_exact_rule(
    clean_desc: str,
    amount: float,
    date_val: Optional[date] = None,
    raw_desc: Optional[str] = None
) -> Optional[ProcessedTransaction]:
    """
    Checks the cleaned description against the exact-match dictionary.
    Supports prefix matching on word boundaries for robustness.
    Returns a ProcessedTransaction with a confidence of 1.0 if matched, otherwise None.
    """
    actual_date = date_val or date.today()
    actual_raw = raw_desc or clean_desc
    
    for rule_key, match_info in EXACT_MATCH_RULES.items():
        # Match if identical or if the cleaned description starts with the key as a word
        if clean_desc == rule_key or clean_desc.startswith(rule_key + " "):
            cat = match_info["category"]
            subcat = match_info.get("sub_category", "Uncategorized")
            intent, impact = derive_intent_and_impact(cat, subcat)
            return ProcessedTransaction(
                date=actual_date,
                raw_description=actual_raw,
                amount=amount,
                clean_merchant=match_info["merchant_name"],
                transaction_type=match_info["transaction_type"],
                category=cat,
                sub_category=subcat,
                intent=intent,
                financial_impact=impact,
                confidence_score=1.0,
                classification_method="rules"
            )
        
    return None

def match_rule(transaction: RawTransaction) -> Optional[ProcessedTransaction]:
    """
    Cleans the raw transaction description and checks it against the exact-match dictionary.
    """
    cleaned_desc = clean_transaction_description(transaction.raw_description)
    return match_exact_rule(
        clean_desc=cleaned_desc,
        amount=transaction.amount,
        date_val=transaction.date,
        raw_desc=transaction.raw_description
    )
