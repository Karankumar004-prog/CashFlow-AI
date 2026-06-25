import pytest
from skills.transaction_understanding.extractor import extract_associated_person

def test_extract_associated_person_for():
    assert extract_associated_person("Books for Raj") == "Raj"
    assert extract_associated_person("Payment for Alice") == "Alice"
    assert extract_associated_person("Payment for Medical") is None  # stop word
    
def test_extract_associated_person_colon():
    assert extract_associated_person("Books: Raj") == "Raj"
    assert extract_associated_person("Expense: Bob") == "Bob"
    
def test_extract_associated_person_comma():
    assert extract_associated_person("Books, Raj") == "Raj"
    assert extract_associated_person("Groceries, Alice") == "Alice"
    
def test_extract_associated_person_to_from():
    assert extract_associated_person("Transfer to John") == "John"
    assert extract_associated_person("Received from Jane") == "Jane"
    
def test_extract_associated_person_none():
    assert extract_associated_person("Just a normal expense") is None
    assert extract_associated_person("Target store") is None
