import json
import urllib.request
import urllib.error
from skills.core.models import RawTransaction, ProcessedTransaction
from skills.data_cleaning.cleaner import clean_transaction_description
from skills.transaction_understanding import rules
from skills.transaction_understanding import regex
from skills.knowledge_layer import memory
from skills.transaction_understanding.validator import validate_transaction
from skills.transaction_understanding.extractor import extract_associated_person

class TransactionType:
    EXPENSE = "Expense"
    INCOME = "Income"
    TRANSFER = "Transfer"
    INVESTMENT = "Investment"
    LOAN_DEBT = "Loan/Debt"
    REFUND = "Refund"

class TransactionCategory:
    FOOD = "Food"
    SHOPPING = "Shopping"
    MEDICAL = "Medical"
    HOUSING = "Housing"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    INVESTMENT = "Investment"
    INCOME = "Income"
    TRANSFER = "Transfer"
    LOAN_DEBT = "Loan/Debt"
    OTHER = "Other"

def _map_csv_metadata(raw_tx: RawTransaction):
    mapped_type = None
    if raw_tx.csv_type:
        t_low = raw_tx.csv_type.lower()
        if 'expense' in t_low or 'debit' in t_low or 'dr' in t_low:
            mapped_type = TransactionType.EXPENSE
        elif 'income' in t_low or 'credit' in t_low or 'cr' in t_low:
            mapped_type = TransactionType.INCOME
        elif 'transfer' in t_low:
            mapped_type = TransactionType.TRANSFER
        elif 'investing' in t_low or 'investments' in t_low:
            mapped_type = TransactionType.INVESTMENT
        elif 'dividends' in t_low:
            mapped_type = TransactionType.INCOME
        elif 'lending' in t_low:
            mapped_type = TransactionType.LOAN_DEBT
            
    mapped_cat = None
    if raw_tx.csv_category:
        c_low = raw_tx.csv_category.lower()
        if c_low in ['food', 'groceries', 'dining', 'restaurant']:
            mapped_cat = TransactionCategory.FOOD
        elif c_low in ['shopping', 'electronics', 'clothing']:
            mapped_cat = TransactionCategory.SHOPPING
        elif c_low in ['medical', 'healthcare', 'pharmacy']:
            mapped_cat = TransactionCategory.MEDICAL
        elif c_low in ['rent', 'utilities', 'housing']:
            mapped_cat = TransactionCategory.HOUSING
        elif c_low in ['transport', 'transportation', 'fuel', 'cab']:
            mapped_cat = TransactionCategory.TRANSPORT
        elif c_low in ['entertainment', 'movies', 'games']:
            mapped_cat = TransactionCategory.ENTERTAINMENT
        elif c_low in ['salary', 'freelance', 'business', 'dividends', 'interest', 'bonus']:
            mapped_cat = TransactionCategory.INCOME
        elif c_low in ['savings', 'investments', 'investing', 'mutual funds', 'stocks']:
            mapped_cat = TransactionCategory.INVESTMENT
        elif c_low in ['lending', 'loan', 'emi', 'mortgage', 'debt']:
            mapped_cat = TransactionCategory.LOAN_DEBT

    if raw_tx.csv_category:
        c_low = raw_tx.csv_category.lower()
        if c_low in ['investing', 'investments']:
            mapped_type = TransactionType.INVESTMENT
            mapped_cat = TransactionCategory.INVESTMENT
        elif c_low == 'dividends':
            mapped_type = TransactionType.INCOME
            mapped_cat = TransactionCategory.INCOME
        elif c_low == 'lending':
            mapped_type = TransactionType.LOAN_DEBT
            mapped_cat = TransactionCategory.LOAN_DEBT
            
    return mapped_type, mapped_cat

def process_transaction(raw_tx: RawTransaction, overrides_dict: dict) -> ProcessedTransaction:
    """
    Orchestrates the multi-stage matching pipeline evaluating cash flow direction FIRST.
    Returns a populated ProcessedTransaction object.
    """
    # 1. Money Direction Restrictions
    amount = raw_tx.amount
    allowed_types = []
    if amount > 0:
        allowed_types = [TransactionType.INCOME, TransactionType.REFUND, TransactionType.TRANSFER, TransactionType.LOAN_DEBT]
    elif amount < 0:
        allowed_types = [TransactionType.EXPENSE, TransactionType.INVESTMENT, TransactionType.TRANSFER, TransactionType.LOAN_DEBT]
        
    clean_desc = clean_transaction_description(raw_tx.raw_description)
    
    # 2 & 3 & 4. Match Extract Merchant & Assign Category
    ptx = None
    
    # Stage A: CSV Pre-Classification (Lowest priority but good default)
    mapped_type, mapped_cat = _map_csv_metadata(raw_tx)
    if mapped_type and mapped_cat:
        ptx = ProcessedTransaction(
            date=raw_tx.date,
            raw_description=raw_tx.raw_description,
            amount=raw_tx.amount,
            clean_merchant=raw_tx.raw_description.strip(),
            transaction_type=mapped_type,
            category=mapped_cat,
            sub_category=raw_tx.csv_category or "Uncategorized",
            intent=rules.derive_intent_and_impact(mapped_cat, raw_tx.csv_category or "Uncategorized")[0],
            financial_impact=rules.derive_intent_and_impact(mapped_cat, raw_tx.csv_category or "Uncategorized")[1],
            confidence_score=0.6,
            classification_method="csv_metadata",
            csv_category=raw_tx.csv_category,
            csv_type=raw_tx.csv_type,
            running_balance=raw_tx.running_balance
        )
        
    # Stage B: Regex patterns
    regex_match = regex.match_regex_patterns(clean_desc, amount, raw_tx.date, raw_tx.raw_description)
    if regex_match:
        ptx = regex_match
        
    # Stage C: Exact rules
    rule_match = rules.match_exact_rule(clean_desc, amount, raw_tx.date, raw_tx.raw_description)
    if rule_match:
        ptx = rule_match
        
    # Stage D: User memory override
    mem_match = memory.match_user_memory(clean_desc, overrides_dict, amount, raw_tx.date, raw_tx.raw_description)
    if mem_match:
        ptx = mem_match
        
    # Default Fallback if nothing matched
    if not ptx:
        if amount > 0:
            tx_type = TransactionType.INCOME
            category = TransactionCategory.INCOME
        else:
            tx_type = TransactionType.EXPENSE
            category = TransactionCategory.OTHER
            
        ptx = ProcessedTransaction(
            date=raw_tx.date,
            raw_description=raw_tx.raw_description,
            amount=raw_tx.amount,
            clean_merchant=raw_tx.raw_description.lower(),
            transaction_type=tx_type,
            category=category,
            intent=rules.derive_intent_and_impact(category, "Uncategorized")[0],
            financial_impact=rules.derive_intent_and_impact(category, "Uncategorized")[1],
            confidence_score=0.0,
            classification_method="default"
        )
        
    # Apply direction restrictions to whatever we matched
    if ptx.transaction_type not in allowed_types:
        # Override tx_type based on money direction
        if amount > 0 and ptx.transaction_type == TransactionType.EXPENSE:
            ptx.transaction_type = TransactionType.REFUND
            
        if amount < 0 and ptx.transaction_type == TransactionType.INCOME:
            ptx.transaction_type = TransactionType.EXPENSE
            
        # Ensure it's in allowed types, otherwise fallback
        if ptx.transaction_type not in allowed_types:
            ptx.transaction_type = allowed_types[0]
            ptx.confidence_score *= 0.5  # Penalize confidence for type correction

    # Extract associated person
    associated_person = extract_associated_person(raw_tx.raw_description)
    if associated_person:
        ptx.associated_person = associated_person

    # 5. Validation Layer
    is_valid, warning_msg = validate_transaction(ptx)
    if not is_valid:
        ptx.confidence_score *= 0.4
        ptx.classification_reason = warning_msg
    else:
        ptx.classification_reason = "Passed all validation checks."

    return ptx
