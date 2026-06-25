from datetime import date
from skills.core.models import RawTransaction
from skills.transaction_understanding.rules import match_rule

def test_match_netflix():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="NETFLIX.COM VENDOR SUB CHARGE",
        amount=-15.49
    )
    result = match_rule(tx)
    assert result is not None
    assert result.clean_merchant == "Netflix"
    assert result.transaction_type == "Expense"
    assert result.category == "Entertainment"
    assert result.confidence_score == 1.0
    assert result.classification_method == "rules"

def test_match_landlord_rent():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="ACH WITHDRAWAL LANDLORD RENT",
        amount=-1600.00
    )
    result = match_rule(tx)
    assert result is not None
    assert result.clean_merchant == "Rent"
    assert result.transaction_type == "Expense"
    assert result.category == "Housing"
    assert result.confidence_score == 1.0
    assert result.classification_method == "rules"

def test_no_match():
    tx = RawTransaction(
        date=date(2026, 6, 23),
        raw_description="UNKNOWN MERCHANDISE POS #92049",
        amount=-30.00
    )
    result = match_rule(tx)
    assert result is None
