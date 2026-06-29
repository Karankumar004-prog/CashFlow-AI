import time
from skills.core.models import StateDict
from skills.transaction_understanding.pipeline import process_transaction
from skills.financial_intelligence.pipeline import run_financial_analysis
from skills.financial_intelligence.behavior_pipeline import run_behavior_analysis
from skills.reasoning_layer.pipeline import run_financial_coach
from skills.reporting_layer.pipeline import run_report_generation

def run_pipeline(raw_txs, overrides, api_key, liquid_assets, total_assets, total_liabilities, currency_symbol="$", currency_name="USD"):
    start_time = time.perf_counter()
    
    # Initialize state dictionary
    state = StateDict()
    state.raw_data["currency_symbol"] = currency_symbol
    state.raw_data["currency_name"] = currency_name
    state.user_memory["overrides"] = overrides
    
    # C. First Pass: Deterministic Categorization (Rules, Regex, Memory)
    first_pass_txs = []
    unknown_descriptions = set()
    
    for tx in raw_txs:
        ptx = process_transaction(tx, overrides_dict=state.user_memory.get("overrides", {}))
        if ptx.confidence_score == 0.0:
            unknown_descriptions.add(ptx.raw_description)
        first_pass_txs.append(ptx)
        
    # D. Second Pass: Batch AI Fallback
    ai_mappings = {}
    if unknown_descriptions and api_key and api_key != "mock":
        try:
            import streamlit as st
            from skills.transaction_understanding.ai import batch_classify_transactions
            st.info(f"🧠 Asking AI to categorize {len(unknown_descriptions)} unknown merchants...")
            ai_mappings = batch_classify_transactions(list(unknown_descriptions), api_key=api_key)
        except Exception as e:
            import streamlit as st
            st.error(f"❌ AI Categorization Failed: {e}")
            st.stop() # Force a hard stop so the user sees the error
            
    # E. Apply AI Mappings
    final_transactions = []
    for ptx in first_pass_txs:
        if ptx.confidence_score <= 0.0 and ptx.raw_description in ai_mappings:
            ai_data = ai_mappings[ptx.raw_description]
            proposed_type = ai_data.get("transaction_type", ptx.transaction_type)
            if ptx.amount > 0 and proposed_type not in ["Income", "Refund", "Transfer", "Loan/Debt"]:
                proposed_type = "Income"
            elif ptx.amount < 0 and proposed_type not in ["Expense", "Investment", "Transfer", "Loan/Debt"]:
                proposed_type = "Expense"
            ptx.transaction_type = proposed_type
            ptx.category = ai_data.get("category", ptx.category)
            ptx.sub_category = ai_data.get("sub_category", ptx.sub_category)
            ptx.clean_merchant = ai_data.get("clean_merchant", ptx.clean_merchant)
            ptx.confidence_score = 0.8
            ptx.classification_method = "ai_fallback"
        final_transactions.append(ptx)
        
    state.processed_data["transactions"] = final_transactions
    
    # Determine liquid assets dynamically from final transaction's running balance if not manually overridden
    if liquid_assets == 0.0:
        if len(raw_txs) > 0:
            dynamic_liquid_assets = raw_txs[-1].running_balance
        else:
            dynamic_liquid_assets = 0.0
    else:
        dynamic_liquid_assets = liquid_assets
        
    dynamic_total_assets = total_assets if total_assets > 0.0 else dynamic_liquid_assets
    
    # Execute Financial Analysis (Ratios & Scorecard)
    state = run_financial_analysis(
        state=state,
        liquid_assets=dynamic_liquid_assets,
        total_assets=dynamic_total_assets,
        total_liabilities=total_liabilities
    )
    
    # Execute Behavior Analysis (Concentration & Flags)
    state = run_behavior_analysis(state)
    
    # Execute Financial Coach reasoning agent
    state = run_financial_coach(state, api_key=api_key)
    
    # Execute Report Generation markdown compilation
    report_md = run_report_generation(state)
    
    end_time = time.perf_counter()
    exec_time = end_time - start_time
    
    # Aggregate all input and output tokens
    fallback_in_tokens = sum(tx.prompt_tokens for tx in final_transactions if hasattr(tx, "prompt_tokens") and tx.prompt_tokens)
    fallback_out_tokens = sum(tx.candidates_tokens for tx in final_transactions if hasattr(tx, "candidates_tokens") and tx.candidates_tokens)
    
    coach_in_tokens = state.agent_outputs.get("promptTokenCount", 0)
    coach_out_tokens = state.agent_outputs.get("candidatesTokenCount", 0)
    
    total_in = fallback_in_tokens + coach_in_tokens
    total_out = fallback_out_tokens + coach_out_tokens
    
    # Gemini 2.5 Flash pricing: $0.075 per 1M input tokens and $0.30 per 1M output tokens
    estimated_cost = (total_in * 0.075 / 1_000_000) + (total_out * 0.30 / 1_000_000)
    
    state.processed_data["telemetry"] = {
        "execution_time_sec": round(exec_time, 4),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "estimated_cost_usd": round(estimated_cost, 6)
    }
    
    return state, report_md
