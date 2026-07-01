from typing import List
from skills.core.models import ProcessedTransaction

def calculate_ratios(
    transactions: List[ProcessedTransaction],
    monthly_income: float,
    liquid_assets: float,
    total_assets: float,
    total_liabilities: float
) -> dict:
    """
    Computes core financial ratios based on transactions list and manual asset/liability inputs.
    Ratios: Savings Rate, Debt Ratio, Emergency Runway, and Asset Coverage.
    """
    import datetime
    
    # Filter dates to exclude extreme outliers (> 1 year in the future)
    # This prevents typos (like year 2026 when it's 2023) from inflating months_covered
    if transactions:
        valid_dates = []
        today = datetime.date.today()
        one_year_future = today + datetime.timedelta(days=365)
        for tx in transactions:
            if tx.date <= one_year_future:
                valid_dates.append(tx.date)
                
        if valid_dates:
            date_range_days = (max(valid_dates) - min(valid_dates)).days
            months_covered = max(date_range_days / 30.0, 1.0)
        else:
            months_covered = 1.0
    else:
        months_covered = 1.0

    # 1. Strictly sum only TransactionType.INCOME transactions (excluding Transfers or Investments)
    abs_income_txs = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "income")
    
    # 2. Strictly sum TransactionType.EXPENSE transactions
    abs_total_expenses = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "expense")
    
    # Include ALL outflows for accurate financial picture
    abs_debt_txs = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "loan/debt")
    abs_investment_txs = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "investment")
    abs_refund_txs = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "refund")

    # Normalize to per-month averages for ratios
    safe_months = max(months_covered, 1.0)
    avg_income = abs_income_txs / safe_months
    avg_expenses = abs_total_expenses / safe_months
    avg_debt = abs_debt_txs / safe_months
    avg_investment = abs_investment_txs / safe_months
    avg_refund = abs_refund_txs / safe_months
    # Legacy calculation logic for savings rate has been moved to the bottom
        
    # 3. Debt Ratio (DTI) Calculation
    if avg_income > 0:
        debt_ratio = avg_debt / avg_income
    else:
        debt_ratio = 0.0
        
    # 4. Emergency Runway Calculation
    # liquid_assets / Monthly Essential Expenses (Needs + Loan/Debt payments)
    abs_essential_expenses = sum(
        abs(tx.amount) for tx in transactions 
        if (tx.transaction_type.lower() == "expense" and getattr(tx, 'intent', '').lower() == "essential")
        or tx.transaction_type.lower() == "loan/debt"
        or getattr(tx, 'intent', '').lower() == "debt payment"
    )
    avg_essential_expenses = abs_essential_expenses / safe_months
    
    if avg_essential_expenses > 0:
        emergency_runway = liquid_assets / avg_essential_expenses
    else:
        # If no essential expenses, runway is effectively infinite/very high
        emergency_runway = 999.0
        
    # 5. Asset Coverage Calculation
    # total_assets / total_liabilities
    if total_liabilities > 0:
        asset_coverage = total_assets / total_liabilities
    else:
        asset_coverage = 999.0
        
    # Total money leaving the ecosystem
    total_outflows = abs_total_expenses + abs_debt_txs + abs_investment_txs
    # Total money entering the ecosystem
    total_inflows = abs_income_txs + abs_refund_txs
    
    net_absolute_cash_flow = total_inflows - total_outflows
    
    if total_inflows > 0:
        savings_rate = net_absolute_cash_flow / total_inflows
    else:
        savings_rate = 0.0
        
    return {
        "savings_rate": savings_rate,
        "debt_ratio": debt_ratio,
        "emergency_runway_months": emergency_runway,
        "asset_coverage": asset_coverage,
        "net_cash_flow": net_absolute_cash_flow,
        "monthly_income": avg_income,
        "total_expenses": avg_expenses,
        "total_absolute_income": total_inflows,
        "total_absolute_expenses": total_outflows,
        "net_absolute_cash_flow": net_absolute_cash_flow,
        "months_covered": months_covered
    }
