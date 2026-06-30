from typing import List
from skills.core.models import StateDict, ProcessedTransaction
from .analyzer import (
    calculate_category_concentration,
    detect_risks,
    calculate_income_concentration,
    calculate_weekly_spending,
    get_category_transparency,
    calculate_intent_concentration,
    calculate_impact_concentration,
    calculate_people_summary
)
from skills.financial_intelligence.recurring import detect_recurring_transactions

def run_behavior_analysis(state: StateDict) -> StateDict:
    """
    Orchestrates the Behavior Analysis skill.
    Updates the state with category concentrations and risk flags.
    """
    # 1. Retrieve processed transactions and ratios from state
    raw_txs = state.processed_data.get("transactions", [])
    ratios = state.processed_data.get("ratios", {})
    
    # Standardize dicts to ProcessedTransaction objects
    transactions: List[ProcessedTransaction] = []
    for tx in raw_txs:
        if isinstance(tx, dict):
            transactions.append(ProcessedTransaction(**tx))
        else:
            transactions.append(tx)
            
    # 2. Compute Concentrations & Risks
    concentration = calculate_category_concentration(transactions)
    income_concentration = calculate_income_concentration(transactions)
    risks = detect_risks(transactions, ratios)
    weekly_spending = calculate_weekly_spending(transactions)
    category_transparency = get_category_transparency(transactions)
    intent_concentration = calculate_intent_concentration(transactions)
    impact_concentration = calculate_impact_concentration(transactions)
    
    people_summary = calculate_people_summary(transactions)
    
    # 3. Update StateDict
    if "behavior" not in state.processed_data:
        state.processed_data["behavior"] = {}
        
    state.processed_data["behavior"]["category_concentration"] = concentration
    state.processed_data["behavior"]["income_concentration"] = income_concentration
    state.processed_data["behavior"]["potential_risk_indicators"] = risks
    state.processed_data["behavior"]["weekly_spending"] = weekly_spending
    state.processed_data["behavior"]["category_transparency"] = category_transparency
    state.processed_data["behavior"]["intent_concentration"] = intent_concentration
    state.processed_data["behavior"]["impact_concentration"] = impact_concentration
    state.processed_data["behavior"]["people_summary"] = people_summary
    
    # Detect deterministic recurring payments
    recurring_bills = detect_recurring_transactions(transactions)
    state.processed_data["behavior"]["recurring_bills"] = recurring_bills
    
    return state

