from skills.core.models import StateDict
from skills.reporting_layer.pipeline import run_report_generation

def test_report_generation_output():
    state = StateDict()
    
    # Pre-populate state details
    state.processed_data["financial_health_score"] = 72.5
    state.processed_data["ratios"] = {
        "savings_rate": 0.22,
        "debt_ratio": 0.10,
        "emergency_runway_months": 4.5,
        "asset_coverage": 2.5
    }
    state.processed_data["behavior"] = {
        "category_concentration": [
            {"category": "Needs", "percentage": 55.0},
            {"category": "Wants", "percentage": 45.0}
        ],
        "potential_risk_indicators": [
            "Low Liquidity Shield: Less than 1 month of essential expenses saved."
        ]
    }
    state.agent_outputs = {
        "quick_wins": [
            {
                "title": "Cancel Gym Membership",
                "description": "Cancel unused gym membership.",
                "potential_savings": 50
            }
        ],
        "roadmap": "1. **Emergency Shield**: Save 1 more month."
    }
    
    report = run_report_generation(state)
    
    # Assertions
    assert report is not None
    assert len(report) > 0
    assert "# CashFlow AI Financial Audit Report" in report
    assert "## 1. Financial Health Score: 72.5/100" in report
    assert "## 2. Cash Flow Summary" in report
    assert "## 3. Core Metrics" in report
    assert "## 4. Behavioral Analysis" in report
    assert "## 5. AI Coach Recommendations" in report
    assert "Cancel Gym Membership" in report
    assert "Potential Monthly Savings: $50/mo" in report
    assert "Emergency Shield" in report

    # Test custom currency symbol formatting
    state.raw_data["currency_symbol"] = "₹"
    report_inr = run_report_generation(state)
    assert "Potential Monthly Savings: ₹50/mo" in report_inr
