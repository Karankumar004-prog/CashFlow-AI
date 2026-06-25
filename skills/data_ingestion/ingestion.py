from skills.data_cleaning.schema import detect_schema
import pandas as pd
from datetime import datetime
from typing import List
from skills.core.models import RawTransaction

def safe_float(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    # Clean PNB balance/amount strings
    return float(str(val).replace(',', '').replace('Cr.', '').replace('Dr.', '').strip())

def parse_csv_to_models(file_path: str) -> List[RawTransaction]:
    if file_path.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
        
    # Standardize column headers: strip whitespace
    df.columns = [col.strip() for col in df.columns]
    
    # 1. Detect schema
    schema = detect_schema(df.columns.tolist())
    
    # Verify we have at least date and description
    if not schema["date"]:
        raise ValueError(f"Could not find a valid Date column in headers: {df.columns.tolist()}")
    if not schema["description"]:
        raise ValueError(f"Could not find a valid Description column in headers: {df.columns.tolist()}")
        
    raw_transactions = []
    
    date_col = schema["date"]
    desc_col = schema["description"]
    debit_col = schema["debit"]
    credit_col = schema["credit"]
    balance_col = schema["balance"]
    amount_col = schema["amount"]
    
    for idx, row in df.iterrows():
        # Parse date
        raw_date = row[date_col]
        if pd.isna(raw_date):
            continue
        try:
            if isinstance(raw_date, str):
                parsed_date = pd.to_datetime(raw_date, dayfirst=True).date()
            else:
                parsed_date = raw_date
                if hasattr(parsed_date, 'date'):
                    parsed_date = parsed_date.date()
        except Exception:
            continue
            
        # Parse description
        raw_desc = str(row[desc_col]) if not pd.isna(row[desc_col]) else ""
        
        # Safely extract Category and Type (checking lowercase/original keys in row)
        row_keys_lower = {k.lower().strip(): k for k in row.keys()}
        
        csv_category = ""
        if 'category' in row_keys_lower:
            cat_val = row[row_keys_lower['category']]
            csv_category = str(cat_val).strip() if not pd.isna(cat_val) else ""
            
        csv_type = ""
        if 'type' in row_keys_lower:
            type_val = row[row_keys_lower['type']]
            csv_type = str(type_val).strip().lower() if not pd.isna(type_val) else ""
            
        # Parse running balance
        running_balance = 0.0
        if balance_col and not pd.isna(row[balance_col]):
            bal_str = str(row[balance_col]).replace('Cr.', '').replace('Dr.', '').replace(',', '').strip()
            try:
                running_balance = float(bal_str) if bal_str else 0.0
            except ValueError:
                pass
                
        # Parse amount
        if amount_col:
            val = row[amount_col]
            if pd.isna(val):
                continue
            try:
                amount = safe_float(val)
            except ValueError:
                continue
        else:
            in_val = safe_float(row.get('Cr Amount') or row.get('In') or (row[credit_col] if credit_col else 0.0))
            out_val = safe_float(row.get('Dr Amount') or row.get('Out') or (row[debit_col] if debit_col else 0.0))
            amount = in_val - out_val

        # Sign normalization using csv_type
        if csv_type:
            t = csv_type.lower()
            if any(kw in t for kw in ['debit', 'dr', 'expense', 'withdrawal']):
                amount = -abs(amount)  # Money OUT = negative
            elif any(kw in t for kw in ['credit', 'cr', 'income', 'deposit', 'refund']):
                amount = abs(amount)   # Money IN = positive

        if amount == 0.0:
            continue
            
        raw_transactions.append(
            RawTransaction(
                date=parsed_date,
                raw_description=raw_desc,
                amount=amount,
                csv_category=csv_category,
                csv_type=csv_type,
                running_balance=running_balance
            )
        )
        
    return raw_transactions
