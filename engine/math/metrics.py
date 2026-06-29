from typing import List, Dict
from pydantic import BaseModel
from engine.domain.models import Transaction, Account

class FinancialSnapshot(BaseModel):
    total_assets: float
    total_liabilities: float
    net_worth: float
    monthly_income: float
    monthly_expenses: float
    net_cash_flow: float
    savings_rate: float
    burn_rate_months: float

def calculate_snapshot(accounts: List[Account], transactions: List[Transaction]) -> FinancialSnapshot:
    """
    Deterministically computes a FinancialSnapshot from a Ledger (Accounts and Transactions).
    """
    total_assets = sum(acc.balance for acc in accounts if acc.account_type == 'asset')
    total_liabilities = sum(acc.balance for acc in accounts if acc.account_type == 'liability')
    net_worth = total_assets - total_liabilities
    
    # Simple logic: sum over all provided transactions
    # In a real engine, we'd filter by month/date range
    monthly_income = sum(tx.amount for tx in transactions if tx.transaction_type == 'Income')
    # Expenses are negative amounts
    monthly_expenses = abs(sum(tx.amount for tx in transactions if tx.transaction_type == 'Expense'))
    
    net_cash_flow = monthly_income - monthly_expenses
    
    if monthly_income > 0:
        savings_rate = net_cash_flow / monthly_income
    else:
        savings_rate = 0.0
        
    if monthly_expenses > 0:
        burn_rate = total_assets / monthly_expenses
    else:
        burn_rate = float('inf')
        
    return FinancialSnapshot(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        net_cash_flow=net_cash_flow,
        savings_rate=savings_rate,
        burn_rate_months=burn_rate
    )
