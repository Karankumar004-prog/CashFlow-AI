from typing import List, Dict, Any
from skills.core.models import StateDict, ProcessedTransaction
from .calculator import calculate_ratios
from .scorecard import compute_health_score

def run_financial_analysis(
    state: StateDict,
    liquid_assets: float = 0.0,
    total_assets: float = 0.0,
    total_liabilities: float = 0.0
) -> StateDict:
    """
    Orchestrates the Financial Analysis skill.
    Updates the state with calculated ratios and the Financial Health Score.
    """
    # 1. Retrieve processed transactions, converting dicts to ProcessedTransaction if necessary
    raw_txs = state.processed_data.get("transactions", [])
    transactions: List[ProcessedTransaction] = []
    for tx in raw_txs:
        if isinstance(tx, dict):
            transactions.append(ProcessedTransaction(**tx))
        else:
            transactions.append(tx)
            
    # 2. Extract monthly income if not manually specified in state raw_data
    # We no longer rely on declared_income from raw_data
    monthly_income = sum(abs(tx.amount) for tx in transactions if tx.transaction_type.lower() == "income")
    
    # 3. Fetch assets & liabilities from raw_data if not directly passed in signature
    state_assets = state.raw_data.get("assets", [])
    state_liabilities = state.raw_data.get("liabilities", [])
    
    # Calculate liquid cash savings and total assets from raw_data if not provided
    calculated_liquid = liquid_assets
    calculated_total_assets = total_assets
    calculated_total_liabs = total_liabilities
    
    # If parameters are zero/default, sum them from state lists
    if calculated_liquid == 0.0:
        # Sum cash/savings assets
        calculated_liquid = sum(
            float(asset.get("value", 0.0)) for asset in state_assets
            if asset.get("type", "").lower() in ["cash", "savings", "checking", "liquid"]
        )
    if calculated_total_assets == 0.0:
        calculated_total_assets = sum(float(asset.get("value", 0.0)) for asset in state_assets)
        
    if calculated_total_liabs == 0.0:
        calculated_total_liabs = sum(float(liab.get("balance", 0.0)) for liab in state_liabilities)
        
    # 4. Calculate Ratios
    ratios = calculate_ratios(
        transactions=transactions,
        monthly_income=monthly_income,
        liquid_assets=calculated_liquid,
        total_assets=calculated_total_assets,
        total_liabilities=calculated_total_liabs
    )
    
    # 5. Compute Score
    health_score = compute_health_score(ratios)
    
    # 6. Update StateDict
    state.processed_data["ratios"] = ratios
    state.processed_data["financial_health_score"] = health_score
    
    # Update raw_data assets/liabilities values if they were manually passed
    if liquid_assets > 0.0 or total_assets > 0.0:
        # Check if cash asset already exists
        cash_exists = any(a.get("type") == "Cash" for a in state.raw_data["assets"])
        if not cash_exists and liquid_assets > 0.0:
            state.raw_data["assets"].append({"type": "Cash", "value": liquid_assets, "description": "Liquid Savings"})
            
    return state
