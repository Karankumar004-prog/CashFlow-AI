import json
import os
from datetime import date
from skills.core.models import RawTransaction
from skills.transaction_understanding.pipeline import process_transaction

def test_dataset_integration_run():
    # Define the mock user overrides required for the test cases
    overrides = {
        "TARGET": {
            "merchant_name": "Target",
            "transaction_type": "Expense",
            "category": "Housing"
        },
        "CUSTOM WORK INFLOW": {
            "merchant_name": "Freelance Gig",
            "transaction_type": "Income",
            "category": "Income"
        },
        "CHASE HOME MORTGAGE": {
            "merchant_name": "Mortgage Payment",
            "transaction_type": "Loan/Debt",
            "category": "Loan/Debt"
        },
        "GAP OUTLET": {
            "merchant_name": "Gap Outlet",
            "transaction_type": "Refund",
            "category": "Shopping"
        }
    }
    
    # Load the transaction understanding test dataset
    json_path = os.path.join("sample_data", "transaction_understanding_test.json")
    with open(json_path, "r") as f:
        test_data = json.load(f)
        
    for index, item in enumerate(test_data):
        raw_tx = RawTransaction(
            date=date(2026, 6, 23),
            raw_description=item["raw_description"],
            amount=item["amount"]
        )
        
        # Run through the pipeline orchestrator
        processed = process_transaction(raw_tx, overrides)
        expected = item["expected"]
        
        # Verify correctness
        assert processed.transaction_type == expected["transaction_type"], \
            f"Index {index} ({item['raw_description']}): Expected type '{expected['transaction_type']}', got '{processed.transaction_type}'"
            
        assert processed.category == expected["category"], \
            f"Index {index} ({item['raw_description']}): Expected category '{expected['category']}', got '{processed.category}'"
            
        assert processed.clean_merchant == expected["merchant_name"], \
            f"Index {index} ({item['raw_description']}): Expected merchant '{expected['merchant_name']}', got '{processed.clean_merchant}'"
            
        assert processed.confidence_score == expected["confidence_score"], \
            f"Index {index} ({item['raw_description']}): Expected confidence {expected['confidence_score']}, got {processed.confidence_score}"
