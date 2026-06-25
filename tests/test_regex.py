from datetime import date
from skills.transaction_understanding.regex import match_regex_patterns

def test_match_regex_payroll():
    res = match_regex_patterns("DIRECT DEP PAYROLL ACME CORP", 2500.0)
    assert res is not None
    assert res.clean_merchant == "Payroll"
    assert res.transaction_type == "Income"
    assert res.category == "Income"
    assert res.confidence_score == 0.9
    assert res.classification_method == "regex"

def test_match_regex_amazon_refund():
    res = match_regex_patterns("AMAZON.COM REFUND ORDER #1948293", 42.99)
    assert res is not None
    assert res.clean_merchant == "Amazon"
    assert res.transaction_type == "Refund"
    assert res.category == "Income"

def test_match_regex_amazon_expense():
    res = match_regex_patterns("AMAZON MKTPLACE CHARGE", -54.30)
    assert res is not None
    assert res.clean_merchant == "Amazon"
    assert res.transaction_type == "Expense"
    assert res.category == "Shopping"

def test_match_regex_vanguard():
    res = match_regex_patterns("VANGUARD BUY ETF VTI", -200.0)
    assert res is not None
    assert res.clean_merchant == "Vanguard"
    assert res.transaction_type == "Investment"
    assert res.category == "Investment"

def test_match_regex_student_loan():
    res = match_regex_patterns("DEPT ED STUDENT LOAN PYMT #92842", -250.0)
    assert res is not None
    assert res.clean_merchant == "Student Loan"
    assert res.transaction_type == "Loan/Debt"
    assert res.category == "Loan/Debt"

def test_match_regex_savings_transfer():
    res = match_regex_patterns("ACH TRANSFER TO SAVINGS BANK OF AMERICA", -500.0)
    assert res is not None
    assert res.clean_merchant == "Savings Transfer"
    assert res.transaction_type == "Transfer"
    assert res.category == "Transfer"

def test_match_regex_coned():
    res = match_regex_patterns("CONEDISON UTILITY BILL autopay", -112.50)
    assert res is not None
    assert res.clean_merchant == "ConEd"
    assert res.transaction_type == "Expense"
    assert res.category == "Housing"
    
def test_no_regex_match():
    assert match_regex_patterns("UNKNOWN TRANSACTION DESCR", -10.0) is None
