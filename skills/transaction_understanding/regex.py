import re
from datetime import date
from typing import Optional
from skills.core.models import ProcessedTransaction
from skills.transaction_understanding.rules import derive_intent_and_impact

def match_regex_patterns(
    clean_desc: str,
    amount: float,
    date_val: Optional[date] = None,
    raw_desc: Optional[str] = None
) -> Optional[ProcessedTransaction]:
    """
    Evaluates regular expressions in sequence to match clean transaction descriptions.
    Returns a ProcessedTransaction with a confidence of 0.9 if matched, otherwise None.
    """
    actual_date = date_val or date.today()
    actual_raw = raw_desc or clean_desc
    
    # Predefined list of pattern, merchant, type, category, sub_category
    patterns = [
        (r"PAYROLL|DIRECT DEP|DIR DEP", "Payroll", "Income", "Income", "Salary"),
        (r"AMAZON.*RE(FUND|T|TURN)", "Amazon", "Refund", "Income", "Refund"),
        (r"^REFUND\b", None, "Refund", "Income", "Refund"),
        (r"\b(PHARMACY|APOLLO|CLINIC|HOSPITAL|MEDICINE|MEDICAL|HEALTH|DR\.|DIAGNOSTIC)\b", None, "Expense", "Medical", "Medicine"),
        (r"\b(SWIGGY|ZOMATO|FOODPANDA|RESTAURANT|CAFE|BAKERY)\b", None, "Expense", "Food", "Restaurant"),
        (r"\b(AMAZON|FLIPKART|MYNTRA|MEESHO|MART|STORE)\b", None, "Expense", "Shopping", "General"),
        (r"VANGUARD", "Vanguard", "Investment", "Investment", "SIP"),
        (r"FIDELITY", "Fidelity", "Investment", "Investment", "Shares"),
        (r"STUDENT LOAN|DEPT ED", "Student Loan", "Loan/Debt", "Loan/Debt", "EMI"),
        (r"TRANSFER.*SAVINGS", "Savings Transfer", "Transfer", "Transfer", "Self"),
        (r"CONEDISON|UTILITY", "ConEd", "Expense", "Housing", "Utilities"),
        (r"UBER|OLA|RAPIDO", "Ride Share", "Expense", "Transport", "Cab"),
        (r"PAYTM|PHONEPE|GPAY|\bCRED\b", "Digital Wallet", "Expense", "Other", "Digital Wallet"),
        (r"BLINKIT|ZEPTO|INSTAMART|DUNZO", "Quick Commerce", "Expense", "Food", "Groceries"),
        (r"NETFLIX|PRIME|HOTSTAR|SONYLIV", "Streaming", "Expense", "Entertainment", "Streaming"),
        (r"MAKEMYTRIP|AGODA|OYO|AIRBNB", "Travel", "Expense", "Entertainment", "Travel"),
        (r"ZERODHA|GROWW|UPSTOX|MUTUAL FUND", "Investment", "Investment", "Investment", "Mutual Fund"),
        (r"JIO|AIRTEL|VI\b|BSNL|RECHARGE", "Mobile/Internet", "Expense", "Housing", "Utilities")
    ]
    
    for pattern, merchant, tx_type, category, sub_category in patterns:
        if re.search(pattern, clean_desc, re.IGNORECASE):
            # If merchant is None, extract from description (strip the matched prefix)
            resolved_merchant = merchant
            if resolved_merchant is None:
                # Strip the matched keyword and clean up
                stripped = re.sub(pattern, '', clean_desc, flags=re.IGNORECASE).strip()
                resolved_merchant = stripped.title() if stripped else actual_raw.title()
            return ProcessedTransaction(
                date=actual_date,
                raw_description=actual_raw,
                amount=amount,
                clean_merchant=resolved_merchant,
                transaction_type=tx_type,
                category=category,
                sub_category=sub_category,
                intent=derive_intent_and_impact(category, sub_category)[0],
                financial_impact=derive_intent_and_impact(category, sub_category)[1],
                confidence_score=0.9,
                classification_method="regex"
            )
            
    return None
