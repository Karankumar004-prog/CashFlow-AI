from skills.core.models import StateDict
from skills.reasoning_layer.pipeline import run_financial_coach

def test_financial_coach_mock_run():
    state = StateDict()
    
    # Setup processed statistics in state
    state.processed_data["financial_health_score"] = 62.5
    state.processed_data["ratios"] = {
        "savings_rate": 0.12,
        "debt_ratio": 0.15,
        "emergency_runway_months": 2.5,
        "asset_coverage": 1.5
    }
    state.processed_data["behavior"] = {
        "category_concentration": [
            {"category": "Wants", "percentage": 45.0},
            {"category": "Needs", "percentage": 55.0}
        ],
        "potential_risk_indicators": [
            "Low Liquidity Shield: Less than 1 month of essential expenses saved."
        ]
    }
    
    # Run the coach orchestrator in mock mode
    updated_state = run_financial_coach(state, api_key="mock")
    
    # Assertions
    outputs = updated_state.agent_outputs
    assert outputs is not None
    assert len(outputs["quick_wins"]) == 3
    assert outputs["quick_wins"][0]["title"] == "Cancel Streaming Sprawl"
    assert outputs["quick_wins"][0]["potential_savings"] == 15
    assert "Secure the Shield" in outputs["roadmap"]
