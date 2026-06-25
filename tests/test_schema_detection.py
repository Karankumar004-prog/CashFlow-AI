from skills.data_ingestion.ingestion import detect_schema

def test_schema_detection_real_headers():
    headers = [
        "txn no.",
        "txn date",
        "description",
        "unnamed: 3",
        "branch name",
        "cheque no.",
        "dr amount",
        "cr amount",
        "balance"
    ]
    
    schema = detect_schema(headers)
    assert schema["date"] == "txn date"
    assert schema["description"] == "description"
    assert schema["debit"] == "dr amount"
    assert schema["credit"] == "cr amount"
    assert schema["balance"] == "balance"
    assert schema["amount"] is None

def test_schema_detection_standard_headers():
    headers = [
        "Date",
        "Particulars",
        "Withdrawal",
        "Deposit",
        "Balance"
    ]
    schema = detect_schema(headers)
    assert schema["date"] == "Date"
    assert schema["description"] == "Particulars"
    assert schema["debit"] == "Withdrawal"
    assert schema["credit"] == "Deposit"
    assert schema["balance"] == "Balance"
