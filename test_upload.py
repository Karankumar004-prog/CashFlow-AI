import sys
from skills.data_ingestion.ingestion import parse_csv_to_models
from skills.data_cleaning.pipeline import clean_transactions
from skills.transaction_understanding.pipeline import process_transaction
from skills.financial_intelligence.pipeline import run_financial_analysis
from skills.core.models import StateDict

try:
    raw_txs = parse_csv_to_models('sample_data/PNBONE_STMT_XX9575_23062026.xl-1.csv')
    print(f"Parsed {len(raw_txs)} transactions.")
    cleaned_txs = clean_transactions(raw_txs)
    print(f"Cleaned {len(cleaned_txs)} transactions.")
    
    processed = []
    for tx in cleaned_txs:
        processed.append(process_transaction(tx, {}))
    print(f"Processed {len(processed)} transactions.")
    
    state = StateDict()
    state.processed_data["transactions"] = processed
    state = run_financial_analysis(state)
    print("Financial analysis successful.")
    
except Exception as e:
    import traceback
    traceback.print_exc()
