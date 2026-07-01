from datetime import date
from skills.core.models import RawTransaction
from skills.transaction_understanding.pipeline import process_transaction

def test_pipeline_rules():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="NETFLIX.COM VENDOR SUB CHARGE",
        amount=-15.49
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "rules"
    assert res.clean_merchant == "Netflix"
    assert res.transaction_type == "Expense"
    assert res.category == "Entertainment"
    assert res.confidence_score == 1.0

def test_pipeline_regex():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="AMAZON MKTPLACE CHARGE",
        amount=-54.30
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "regex"
    assert res.clean_merchant == "Amazon"
    assert res.transaction_type == "Expense"
    assert res.category == "Shopping"
    assert res.confidence_score == 0.9

def test_pipeline_memory():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="OVERRIDE TARGET STORE CHARGE",
        amount=-89.40
    )
    overrides = {
        "TARGET": {
            "merchant_name": "Target",
            "transaction_type": "Expense",
            "category": "Needs"
        }
    }
    res = process_transaction(tx, overrides)
    assert res.classification_method == "memory"
    assert res.clean_merchant == "Target"
    assert res.transaction_type == "Expense"
    assert res.category == "Needs"
    assert res.confidence_score == 0.95

def test_pipeline_fallback_expense():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="UNKNOWN MERCHANDISE POS #92049",
        amount=-30.00
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "default"
    assert res.clean_merchant == "unknown merchandise pos #92049"
    assert res.transaction_type == "Expense"
    assert res.category == "Other"
    assert res.confidence_score == 0.18

def test_pipeline_fallback_income():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="MYSTERY INFLOW CREDIT",
        amount=100.00
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "default"
    assert res.clean_merchant == "mystery inflow credit"
    assert res.transaction_type == "Income"
    assert res.category == "Income"
    assert res.confidence_score == 0.18

def test_pipeline_ai_fallback():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="RANDOM COFFEE SHOP STARBUCKS #123",
        amount=-4.50
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "default"
    assert res.category == "Other"
    assert res.confidence_score == 0.18

def test_pipeline_telemetry():
    from app import run_pipeline
    txs = [
        RawTransaction(
            date=date(2026, 6, 23),
            raw_description="NETFLIX.COM VENDOR SUB CHARGE",
            amount=-15.49
        )
    ]
    state, report_md = run_pipeline(
        raw_txs=txs,
        overrides={},
        api_key="mock",
        liquid_assets=12000.0,
        total_assets=15000.0,
        total_liabilities=5000.0
    )
    
    telemetry = state.processed_data.get("telemetry", {})
    assert "execution_time_sec" in telemetry
    assert telemetry["execution_time_sec"] >= 0.0
    assert telemetry["total_input_tokens"] == 0
    assert telemetry["total_output_tokens"] == 0
    assert telemetry["estimated_cost_usd"] == 0.0

def test_pipeline_csv_metadata_classification():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="RANDOM COFFEE SHOP STARBUCKS #123",
        amount=-4.50,
        csv_category="food",
        csv_type="expense"
    )
    res = process_transaction(tx, {})
    assert res.classification_method == "csv_metadata"
    assert res.transaction_type == "Expense"
    assert res.category == "Food"
    assert res.confidence_score == 0.6

def test_pipeline_new_stage0_mappings():
    # 1. Test investing mapping
    tx1 = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="Brokerage Deposit",
        amount=-1000.0,
        csv_category="investing"
    )
    res1 = process_transaction(tx1, {})
    assert res1.classification_method == "csv_metadata"
    assert res1.transaction_type == "Investment"
    assert res1.category == "Investment"
    
    # 2. Test dividends mapping
    tx2 = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="Company Stock Dividend",
        amount=150.0,
        csv_category="dividends"
    )
    res2 = process_transaction(tx2, {})
    assert res2.classification_method == "csv_metadata"
    assert res2.transaction_type == "Income"
    assert res2.category == "Income"
    
    # 3. Test lending mapping
    tx3 = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="Peer to peer lending",
        amount=-200.0,
        csv_category="lending"
    )
    res3 = process_transaction(tx3, {})
    assert res3.classification_method == "csv_metadata"
    assert res3.transaction_type == "Loan/Debt"
    assert res3.category == "Loan/Debt"



