MERCHANT_MEMORY = {
    "NEXTBILLION": {"clean_merchant": "Groww (Nextbillion)", "category": "Investment", "intent": "Wealth Building", "financial_impact": "Wealth Building"},
    "MCDONALDS": {"clean_merchant": "McDonald's", "category": "Food", "intent": "Lifestyle", "financial_impact": "Variable Expense"}
}

def check_merchant_memory(raw_desc: str):
    if not raw_desc: return None
    raw_upper = raw_desc.upper()
    for key, metadata in MERCHANT_MEMORY.items():
        if key in raw_upper:
            return metadata
    return None
