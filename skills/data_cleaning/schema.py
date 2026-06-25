from typing import List

def detect_schema(columns: List[str]) -> dict:
    """
    Analyzes list of column headers (case-insensitive) and maps them to a normalized internal schema.
    Returns a dict with keys: 'date', 'description', 'debit', 'credit', 'balance', 'amount'.
    """
    schema = {
        "date": None,
        "description": None,
        "debit": None,
        "credit": None,
        "balance": None,
        "amount": None
    }
    
    # Lowercase all columns for matching
    cols_lower = [c.lower().strip() for c in columns]
    
    # 1. Date column
    date_patterns = ['txn date', 'transaction date', 'date', 'post date', 'booking date', 'value date']
    for pattern in date_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            schema["date"] = columns[idx]
            break
    if not schema["date"]:
        # Fallback substring match
        for idx, col in enumerate(cols_lower):
            if 'date' in col:
                schema["date"] = columns[idx]
                break
                
    # 2. Description column
    desc_patterns = ['description', 'particulars', 'payee', 'memo', 'details', 'name', 'merchant', 'note']
    for pattern in desc_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            schema["description"] = columns[idx]
            break
    if not schema["description"]:
        for idx, col in enumerate(cols_lower):
            if 'desc' in col or 'particular' in col or 'details' in col:
                schema["description"] = columns[idx]
                break
                
    # 3. Debit (Out) column
    debit_patterns = ['dr amount', 'debit', 'withdrawal', 'spent', 'out', 'outflow', 'dr']
    for pattern in debit_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            schema["debit"] = columns[idx]
            break
    if not schema["debit"]:
        for idx, col in enumerate(cols_lower):
            if 'debit' in col or 'withdrawal' in col or col == 'dr' or col.startswith('dr ') or col.endswith(' dr'):
                schema["debit"] = columns[idx]
                break
                
    # 4. Credit (In) column
    credit_patterns = ['cr amount', 'credit', 'deposit', 'received', 'in', 'inflow', 'cr']
    for pattern in credit_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            schema["credit"] = columns[idx]
            break
    if not schema["credit"]:
        for idx, col in enumerate(cols_lower):
            if 'credit' in col or 'deposit' in col or col == 'cr' or col.startswith('cr ') or col.endswith(' cr'):
                schema["credit"] = columns[idx]
                break
                
    # 5. Balance column
    bal_patterns = ['balance', 'bal', 'running balance', 'outstanding']
    for pattern in bal_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            schema["balance"] = columns[idx]
            break
    if not schema["balance"]:
        for idx, col in enumerate(cols_lower):
            if col == 'bal' or 'balance' in col:
                schema["balance"] = columns[idx]
                break
                
    # 6. Single Amount column (fallback if no separate debit/credit)
    amt_patterns = ['amount', 'value', 'charge', 'txn amount', 'tx amount']
    for pattern in amt_patterns:
        if pattern in cols_lower:
            idx = cols_lower.index(pattern)
            if columns[idx] not in (schema["date"], schema["description"], schema["debit"], schema["credit"], schema["balance"]):
                schema["amount"] = columns[idx]
                break
    if not schema["amount"]:
        for idx, col in enumerate(cols_lower):
            if columns[idx] in (schema["date"], schema["description"], schema["debit"], schema["credit"], schema["balance"]):
                continue
            if 'amount' in col or 'value' in col:
                schema["amount"] = columns[idx]
                break
                
    return schema
