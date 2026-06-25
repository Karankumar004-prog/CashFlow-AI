from skills.data_cleaning.cleaner import clean_transaction_description

def test_clean_prefixes():
    assert clean_transaction_description("POS PUR STARBUCKS") == "STARBUCKS"
    assert clean_transaction_description("DEBIT CARD PURCHASE NETFLIX") == "NETFLIX"
    assert clean_transaction_description("CHECK CARD CHRONIC TACOS") == "CHRONIC TACOS"
    assert clean_transaction_description("ACH WITHDRAWAL LANDLORD RENT") == "LANDLORD RENT"

def test_clean_numbers_and_hashes():
    assert clean_transaction_description("STARBUCKS #1249") == "STARBUCKS"
    assert clean_transaction_description("AMAZON # 98402") == "AMAZON"
    assert clean_transaction_description("NETFLIX VENDOR CHARGE 284920") == "NETFLIX"

def test_clean_states_and_utilities():
    assert clean_transaction_description("STARBUCKS SEATTLE WA") == "STARBUCKS"
    assert clean_transaction_description("CHRONIC TACOS ALISO VIEJO CA") == "CHRONIC TACOS"
    assert clean_transaction_description("CONEDISON UTILITY BILL autopay") == "CONEDISON UTILITY"
    assert clean_transaction_description("NETFLIX.COM SUB CHARGE") == "NETFLIX"

def test_clean_empty():
    assert clean_transaction_description("") == ""
    assert clean_transaction_description(None) == ""
