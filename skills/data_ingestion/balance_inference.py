import pandas as pd

def extract_balances_from_csv(file_path: str) -> dict:
    """
    Attempts to parse Account and Balance columns from the CSV
    to infer assets and liabilities.
    """
    try:
        df = pd.read_csv(file_path)
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Look for Date column
        date_col = None
        for name in ['date', 'transaction date', 'txn date', 'post date', 'booking date']:
            if name in df.columns:
                date_col = name
                break
                
        # Look for Account column
        acc_col = None
        for name in ['account', 'acc', 'card', 'wallet', 'account name']:
            if name in df.columns:
                acc_col = name
                break
                
        # Look for Balance column
        bal_col = None
        for name in ['balance', 'bal', 'running balance', 'outstanding']:
            if name in df.columns:
                bal_col = name
                break
                
        if not acc_col or not bal_col:
            return {}
            
        # Parse dates to sort correctly
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(by=date_col)
            
        # Get the last row for each account
        latest_rows = df.groupby(acc_col).last().reset_index()
        
        balances = {}
        for _, row in latest_rows.iterrows():
            acc_name = str(row[acc_col])
            try:
                bal_val = float(row[bal_col])
                balances[acc_name] = bal_val
            except (ValueError, TypeError):
                pass
                
        # Classify as assets and liabilities
        liquid_savings = 0.0
        calculated_assets = 0.0
        calculated_liabilities = 0.0
        
        for acc_name, bal in balances.items():
            name_lower = acc_name.lower()
            is_credit_account = any(kw in name_lower for kw in ['credit card', 'credit', 'cc', 'visa', 'mastercard', 'amex', 'discover'])
            if is_credit_account:
                # Credit card balances are amounts OWED (liabilities), even if positive
                calculated_liabilities += abs(bal)
            elif bal > 0:
                calculated_assets += bal
                if any(x in name_lower for x in ['savings', 'checking', 'emergency', 'cash', 'liquid']):
                    liquid_savings += bal
            else:
                calculated_liabilities += abs(bal)
                
        # If liquid savings was not set but we have assets, default liquid savings to total positive assets
        if liquid_savings == 0.0 and calculated_assets > 0.0:
            liquid_savings = calculated_assets
            
        return {
            "liquid_assets": liquid_savings,
            "total_assets": calculated_assets,
            "total_liabilities": calculated_liabilities
        }
    except Exception:
        return {}
