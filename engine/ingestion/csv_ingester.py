import pandas as pd
import re
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from engine.domain.models import Transaction
from engine.ingestion.base import IngestionStrategy
from skills.data_cleaning.schema import detect_schema

def safe_float(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d\.-]', '', str(val))
    return float(clean_val) if clean_val else 0.0

class CSVIngester(IngestionStrategy):
    def ingest(self, file_path: str, account_id: int, db: Session) -> List[Transaction]:
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        df.columns = [str(col).strip() for col in df.columns]
        schema = detect_schema(df.columns.tolist())
        
        if not schema["date"] or not schema["description"]:
            raise ValueError(f"Could not find valid Date and Description columns in headers: {df.columns.tolist()}")
            
        transactions = []
        date_col = schema["date"]
        desc_col = schema["description"]
        debit_col = schema["debit"]
        credit_col = schema["credit"]
        amount_col = schema["amount"]
        
        for idx, row in df.iterrows():
            raw_date = row[date_col]
            if pd.isna(raw_date):
                continue
            
            try:
                if isinstance(raw_date, str):
                    if re.match(r'^\d{4}-\d{2}-\d{2}', str(raw_date).strip()):
                        parsed_date = pd.to_datetime(raw_date).date()
                    else:
                        parsed_date = pd.to_datetime(raw_date, dayfirst=True).date()
                else:
                    parsed_date = raw_date
                    if hasattr(parsed_date, 'date'):
                        parsed_date = parsed_date.date()
            except Exception:
                continue
                
            raw_desc = str(row[desc_col]) if not pd.isna(row[desc_col]) else ""
            
            row_keys_lower = {str(k).lower().strip(): k for k in row.keys()}
            
            csv_category = ""
            if 'category' in row_keys_lower:
                cat_val = row[row_keys_lower['category']]
                csv_category = str(cat_val).strip() if not pd.isna(cat_val) else ""
                
            csv_type = ""
            if 'type' in row_keys_lower:
                type_val = row[row_keys_lower['type']]
                csv_type = str(type_val).strip().lower() if not pd.isna(type_val) else ""
                
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

            if csv_type:
                t = csv_type.lower()
                if any(kw in t for kw in ['debit', 'dr', 'expense', 'withdrawal']):
                    amount = -abs(amount)
                elif any(kw in t for kw in ['credit', 'cr', 'income', 'deposit', 'refund']):
                    amount = abs(amount)

            if amount == 0.0:
                continue
                
            txn = Transaction(
                account_id=account_id,
                date=parsed_date,
                raw_description=raw_desc,
                amount=amount,
                # We can store csv_category/type in a generic way, but for now we rely on deterministic engine to fill clean_merchant, transaction_type etc.
            )
            transactions.append(txn)
            
        return transactions
