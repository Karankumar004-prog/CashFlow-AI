from skills.knowledge_layer.memory import match_user_memory

def test_match_user_memory_success():
    overrides = {
        "TARGET": {
            "merchant_name": "Target",
            "transaction_type": "Expense",
            "category": "Needs"
        }
    }
    res = match_user_memory("TARGET", overrides, -45.0)
    assert res is not None
    assert res.clean_merchant == "Target"
    assert res.transaction_type == "Expense"
    assert res.category == "Needs"
    assert res.confidence_score == 0.95
    assert res.classification_method == "memory"

def test_match_user_memory_fail():
    overrides = {
        "TARGET": {
            "merchant_name": "Target",
            "transaction_type": "Expense",
            "category": "Needs"
        }
    }
    res = match_user_memory("WALMART", overrides, -12.5)
    assert res is None
