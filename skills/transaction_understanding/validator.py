from typing import Tuple
from skills.core.models import ProcessedTransaction

def validate_transaction(ptx: ProcessedTransaction) -> Tuple[bool, str]:
    """
    Validates a ProcessedTransaction against strict financial logic rules.
    Returns a tuple of (is_valid, warning_message).
    """
    warnings = []
    
    amount = ptx.amount
    tx_type = ptx.transaction_type
    cat = ptx.category
    
    # 1. Cash Flow Direction Mismatches
    if amount > 0:
        if tx_type in ["Expense", "Investment", "Transfer Out", "Loan Given"]:
            warnings.append(f"Positive cash flow (+{amount}) cannot be typed as '{tx_type}'")
    elif amount < 0:
        if tx_type in ["Income", "Refund", "Transfer In", "Loan Repayment"]:
            warnings.append(f"Negative cash flow ({amount}) cannot be typed as '{tx_type}'")
            
    # 2. Category Contradictions
    if amount < 0 and cat in ["Income", "Salary", "Refund"]:
        warnings.append(f"Negative cash flow cannot belong to category '{cat}'")
        
    if tx_type == "Transfer" and cat not in ["Family", "Transfer", "Savings", "Investment", "Loan/Debt", "Other"]:
        warnings.append(f"Transfers should generally not be categorized as '{cat}' unless explicitly mapped")
        
    intent = getattr(ptx, 'intent', '')
    impact = getattr(ptx, 'financial_impact', '')
    
    # 3. Intent & Impact Contradictions
    if amount < 0 and impact == "Wealth Building" and tx_type != "Investment":
        warnings.append(f"Wealth Building impact usually requires Investment or Income, not '{tx_type}'")
        
    if warnings:
        return False, " | ".join(warnings)
        
    return True, ""
