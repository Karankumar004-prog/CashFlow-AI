from typing import List, Dict, Any
from skills.core.models import StateDict
from .agent import generate_coach_advice

def run_financial_coach(state: StateDict, api_key: str = None) -> StateDict:
    """
    Orchestrates the Financial Coach skill.
    Updates the state's agent_outputs with the generated Quick Wins and Roadmap.
    """
    # 1. Extract values from state
    score = state.processed_data.get("financial_health_score", 0.0)
    ratios = state.processed_data.get("ratios", {})
    
    behavior = state.processed_data.get("behavior", {})
    concentrations = behavior.get("category_concentration", [])
    
    # Retrieve top 3 spending concentrations
    top_categories = concentrations[:3]
    
    risk_flags = behavior.get("potential_risk_indicators", [])
    
    currency_symbol = state.raw_data.get("currency_symbol", "$")
    
    income_concentration = behavior.get("income_concentration", [])
    net_cash_flow = ratios.get("net_absolute_cash_flow", ratios.get("net_cash_flow", 0.0))
    monthly_income = ratios.get("total_absolute_income", ratios.get("monthly_income", 0.0))
    total_expenses_val = ratios.get("total_absolute_expenses", ratios.get("total_expenses", 0.0))
    months_covered = ratios.get("months_covered", 1.0)
    
    # 2. Query Gemini / Mock Coach Advice
    advice = generate_coach_advice(
        financial_health_score=score,
        ratios=ratios,
        top_categories=top_categories,
        risk_flags=risk_flags,
        api_key=api_key,
        currency_symbol=currency_symbol,
        income_concentration=income_concentration,
        net_cash_flow=net_cash_flow,
        monthly_income=monthly_income,
        total_expenses=total_expenses_val,
        months_covered=months_covered
    )
    
    # 3. Update state agent_outputs dictionary
    if not state.agent_outputs:
        state.agent_outputs = {}
        
    state.agent_outputs["quick_wins"] = advice.get("quick_wins", [])
    state.agent_outputs["roadmap"] = advice.get("roadmap", "")
    state.agent_outputs["promptTokenCount"] = advice.get("promptTokenCount", 0)
    state.agent_outputs["candidatesTokenCount"] = advice.get("candidatesTokenCount", 0)
    
    return state
