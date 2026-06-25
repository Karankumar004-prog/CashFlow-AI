from datetime import date
from skills.core.models import StateDict, ProcessedTransaction
from skills.financial_intelligence.calculator import calculate_ratios
from skills.financial_intelligence.scorecard import compute_health_score
from skills.financial_intelligence.pipeline import run_financial_analysis

def test_calculator_savings_rate():
    # Test transactions
    txs = [
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Payroll",
            amount=4000.0,
            clean_merchant="Payroll",
            transaction_type="Income",
            category="Income",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Rent",
            amount=-1600.0,
            clean_merchant="Rent",
            transaction_type="Expense",
            category="Housing",
            intent="Essential",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Starbucks",
            amount=-400.0,
            clean_merchant="Starbucks",
            transaction_type="Expense",
            category="Food",
            intent="Lifestyle",
            confidence_score=1.0,
            classification_method="rules"
        )
    ]
    
    ratios = calculate_ratios(
        transactions=txs,
        monthly_income=4000.0,
        liquid_assets=12000.0,
        total_assets=15000.0,
        total_liabilities=0.0
    )
    
    # Savings Rate: (4000 - 2000) / 4000 = 0.50 (50%)
    assert ratios["savings_rate"] == 0.50
    # Debt ratio: 0.0 (no Loan/Debt type transactions)
    assert ratios["debt_ratio"] == 0.0
    # Runway: 12000 / 1600 = 7.5 months (essential expense is Rent=1600 since Starbucks=Wants is excluded)
    assert ratios["emergency_runway_months"] == 7.5
    # Asset coverage: 999.0 (liabilities is 0)
    assert ratios["asset_coverage"] == 999.0
    # Net Cash Flow: 4000.0 - 2000.0 = 2000.0
    assert ratios["net_cash_flow"] == 2000.0

def test_scorecard_points():
    # Case 1: All optimal metrics -> Should score 100
    optimal = {
        "savings_rate": 0.25,
        "debt_ratio": 0.10,
        "emergency_runway_months": 8.0,
        "asset_coverage": 4.0
    }
    assert compute_health_score(optimal) == 100.0
    
    # Case 2: Intermediate scores -> Should score 50.0 (12.5pt each)
    intermediate = {
        "savings_rate": 0.10,            # 0.10 * 125 = 12.5
        "debt_ratio": 0.325,             # 25 - ((0.175/0.35) * 25) = 12.5
        "emergency_runway_months": 3.0,  # (3 / 6) * 25 = 12.5
        "asset_coverage": 2.0            # ((2.0 - 1.0) / 2.0) * 25 = 12.5
    }
    assert compute_health_score(intermediate) == 50.0
    
    # Case 3: Extreme poor scores -> Should score 0
    poor = {
        "savings_rate": -0.10,
        "debt_ratio": 0.60,
        "emergency_runway_months": 0.0,
        "asset_coverage": 0.5
    }
    assert compute_health_score(poor) == 0.0

def test_pipeline_integration():
    state = StateDict()
    state.processed_data["transactions"] = [
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Salary",
            amount=5000.0,
            clean_merchant="Salary",
            transaction_type="Income",
            category="Income",
            confidence_score=0.9,
            classification_method="regex"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Rent",
            amount=-2000.0,
            clean_merchant="Rent",
            transaction_type="Expense",
            category="Housing",
            intent="Essential",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Student Loan",
            amount=-1000.0,
            clean_merchant="Student Loan",
            transaction_type="Loan/Debt",
            category="Loan/Debt",
            intent="Debt Payment",
            confidence_score=0.9,
            classification_method="regex"
        )
    ]
    
    # Pass assets and liabilities directly to pipeline
    updated_state = run_financial_analysis(
        state=state,
        liquid_assets=6000.0,
        total_assets=10000.0,
        total_liabilities=5000.0
    )
    
    ratios = updated_state.processed_data["ratios"]
    score = updated_state.processed_data["financial_health_score"]
    
    # Monthly Income: 5000.0
    # Total Expense: 2000.0, Debt: 1000.0 -> total_outflows = 3000.0
    # Savings Rate: (5000 + 0 - 3000) / 5000 = 0.40
    assert ratios["savings_rate"] == 0.40
    
    # Debt payments: 1000.0
    # Debt ratio: 1000 / 5000 = 0.20
    assert ratios["debt_ratio"] == 0.20
    
    # Essential expenses: Rent (2000) + Student Loan (1000) = 3000
    # Runway: 6000 / 3000 = 2.0 months
    assert ratios["emergency_runway_months"] == 2.0
    
    # Asset coverage: 10000 / 5000 = 2.0
    assert ratios["asset_coverage"] == 2.0
    
    # Score:
    # Savings: min(0.40, 0.20) * 125 = 25pt
    # Debt: 25 - (((0.20-0.15)/0.35) * 25) = 25 - 3.57 = 21.43pt
    # Runway: (2/6) * 25 = 8.33pt
    # Asset: ((2.0-1.0)/2.0) * 25 = 12.5pt
    # Total: 25 + 21.43 + 8.33 + 12.5 = 67.26
    assert 67.0 < score < 67.5
