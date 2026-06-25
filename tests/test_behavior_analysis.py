from datetime import date
from skills.core.models import StateDict, ProcessedTransaction
from skills.financial_intelligence.analyzer import calculate_category_concentration, detect_risks
from skills.financial_intelligence.behavior_pipeline import run_behavior_analysis

def test_category_concentration_math():
    txs = [
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Rent",
            amount=-1500.0,
            clean_merchant="Rent",
            transaction_type="Expense",
            category="Needs",
            sub_category="Housing",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Starbucks",
            amount=-300.0,
            clean_merchant="Starbucks",
            transaction_type="Expense",
            category="Wants",
            sub_category="Coffee",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Netflix",
            amount=-200.0,
            clean_merchant="Netflix",
            transaction_type="Expense",
            category="Wants",
            sub_category="Entertainment",
            confidence_score=1.0,
            classification_method="rules"
        )
    ]
    
    concentration = calculate_category_concentration(txs)
    
    # Total expense = 1500 + 300 + 200 = 2000
    # Housing: 1500 / 2000 = 75.0%
    # Coffee: 300 / 2000 = 15.0%
    # Entertainment: 200 / 2000 = 10.0%
    assert len(concentration) == 3
    assert concentration[0]["category"] == "Housing"
    assert concentration[0]["percentage"] == 75.0
    assert concentration[1]["category"] == "Coffee"
    assert concentration[1]["percentage"] == 15.0
    assert concentration[2]["category"] == "Entertainment"
    assert concentration[2]["percentage"] == 10.0
    
    # Sum of percentages should be exactly 100
    total_pct = sum(c["percentage"] for c in concentration)
    assert total_pct == 100.0

def test_risk_deficit_and_liquidity():
    ratios = {
        "savings_rate": -0.05,
        "emergency_runway_months": 0.5,
        "debt_ratio": 0.0,
        "asset_coverage": 999.0
    }
    
    risks = detect_risks([], ratios)
    assert len(risks) == 2
    assert "Cash Flow Deficit: Outflows exceed income." in risks
    assert "Low Liquidity Shield: Less than 1 month of essential expenses saved." in risks

def test_risk_subscription_sprawl():
    # Construct 6 unique merchants with 2 identical transaction amounts each
    merchants = ["Netflix", "Spotify", "Hulu", "Gym", "Github", "Dropbox"]
    txs = []
    
    for m in merchants:
        for _ in range(2):
            txs.append(
                ProcessedTransaction(
                    date=date(2026, 6, 23),
                    raw_description=m,
                    amount=-10.0,
                    clean_merchant=m,
                    transaction_type="Expense",
                    category="Wants",
                    confidence_score=1.0,
                    classification_method="rules"
                )
            )
            
    # Add an extra random transaction that is single (not recurring)
    txs.append(
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Gas Station",
            amount=-45.0,
            clean_merchant="Shell",
            transaction_type="Expense",
            category="Needs",
            confidence_score=0.9,
            classification_method="regex"
        )
    )
    
    ratios = {"savings_rate": 0.15, "emergency_runway_months": 3.0}
    
    risks = detect_risks(txs, ratios)
    # Subscription sprawl should trigger because unique recurring count is 6 (> 5)
    assert "Subscription Sprawl: High number of recurring identical charges detected." in risks

def test_pipeline_behavior_integration():
    state = StateDict()
    state.processed_data["transactions"] = [
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Salary",
            amount=4000.0,
            clean_merchant="Salary",
            transaction_type="Income",
            category="Income",
            sub_category="Salary",
            confidence_score=0.9,
            classification_method="regex"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Rent",
            amount=-2200.0,
            clean_merchant="Rent",
            transaction_type="Expense",
            category="Needs",
            sub_category="Housing",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Starbucks",
            amount=-2000.0,
            clean_merchant="Starbucks",
            transaction_type="Expense",
            category="Wants",
            sub_category="Coffee",
            confidence_score=1.0,
            classification_method="rules"
        )
    ]
    
    # Set ratios in state showing deficit and low runway
    state.processed_data["ratios"] = {
        "savings_rate": -0.05,  # (4000 - 4200) / 4000
        "emergency_runway_months": 0.8
    }
    
    updated_state = run_behavior_analysis(state)
    behavior = updated_state.processed_data["behavior"]
    
    # Concentrations: Housing (2200/4200 = 52.38%), Coffee (2000/4200 = 47.62%)
    assert len(behavior["category_concentration"]) == 2
    assert behavior["category_concentration"][0]["category"] == "Housing"
    assert 52.0 < behavior["category_concentration"][0]["percentage"] < 53.0
    
    # Risks: Deficit and Liquidity should both trigger
    risks = behavior["potential_risk_indicators"]
    assert len(risks) == 2
    assert "Cash Flow Deficit: Outflows exceed income." in risks
    assert "Low Liquidity Shield: Less than 1 month of essential expenses saved." in risks

def test_calculate_income_concentration():
    from skills.financial_intelligence.analyzer import calculate_income_concentration
    txs = [
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Employer A payroll",
            amount=3000.0,
            clean_merchant="Employer A",
            transaction_type="Income",
            category="Income",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Employer B payroll",
            amount=1000.0,
            clean_merchant="Employer B",
            transaction_type="Income",
            category="Income",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 23),
            raw_description="Grocery store spend",
            amount=-100.0,
            clean_merchant="Kroger",
            transaction_type="Expense",
            category="Needs",
            confidence_score=1.0,
            classification_method="rules"
        )
    ]
    res = calculate_income_concentration(txs)
    assert len(res) == 2
    assert res[0]["source"] == "EMPLOYER A"
    assert res[0]["percentage"] == 75.0
    assert res[1]["source"] == "EMPLOYER B"
    assert res[1]["percentage"] == 25.0

def test_weekly_spending_and_transparency():
    from skills.financial_intelligence.analyzer import calculate_weekly_spending, get_category_transparency
    txs = [
        ProcessedTransaction(
            date=date(2026, 6, 1), # week 23 (2026-06-01 is Monday)
            raw_description="Rent",
            amount=-1000.0,
            clean_merchant="Rent",
            transaction_type="Expense",
            category="Needs",
            sub_category="Housing",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 2), # week 23
            raw_description="Starbucks",
            amount=-50.0,
            clean_merchant="Starbucks",
            transaction_type="Expense",
            category="Wants",
            sub_category="Coffee",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 8), # week 24
            raw_description="Starbucks",
            amount=-15.0,
            clean_merchant="Starbucks",
            transaction_type="Expense",
            category="Wants",
            sub_category="Coffee",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 15), # week 25
            raw_description="Grocery Store",
            amount=-200.0,
            clean_merchant="Kroger",
            transaction_type="Expense",
            category="Needs",
            sub_category="Groceries",
            confidence_score=1.0,
            classification_method="rules"
        ),
        ProcessedTransaction(
            date=date(2026, 6, 15), # week 25
            raw_description="Salary",
            amount=5000.0,
            clean_merchant="Employer",
            transaction_type="Income",
            category="Income",
            sub_category="Salary",
            confidence_score=1.0,
            classification_method="rules"
        )
    ]
    
    weekly = calculate_weekly_spending(txs)
    assert len(weekly) == 3
    assert weekly[0] == {"week_number": 23, "total_spent": 1050.0}
    assert weekly[1] == {"week_number": 24, "total_spent": 15.0}
    assert weekly[2] == {"week_number": 25, "total_spent": 200.0}
    
    transparency = get_category_transparency(txs)
    assert transparency["Needs > Housing"] == ["Rent"]
    assert transparency["Needs > Groceries"] == ["Kroger"]
    assert transparency["Wants > Coffee"] == ["Starbucks"]
    assert transparency["Income > Salary"] == ["Employer"]


