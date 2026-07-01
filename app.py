import streamlit as st
import pandas as pd
import altair as alt
import tempfile
import os
from datetime import date
import sys
import importlib

# Removed dangerous importlib.reload loop to prevent Streamlit cache state issues

# Import models, parsing, and pipeline orchestration functions
from skills.core.models import StateDict, RawTransaction
from skills.data_ingestion.ingestion import parse_csv_to_models
from skills.data_cleaning.pipeline import clean_transactions
from skills.transaction_understanding.pipeline import process_transaction
from skills.financial_intelligence.pipeline import run_financial_analysis
from skills.financial_intelligence.behavior_pipeline import run_behavior_analysis
from skills.reasoning_layer.pipeline import run_financial_coach
from skills.knowledge_layer.database import init_db
from skills.knowledge_layer.crud import get_all_overrides, upsert_override

init_db()
from skills.reporting_layer.pipeline import run_report_generation
from skills.data_ingestion.balance_inference import extract_balances_from_csv
from skills.core.orchestrator import run_pipeline

# -------------------------------------------------------------
# 1. Page Configuration & Theme Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="CashFlow AI - Financial Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(to right, #6EE7B7, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.85;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Card/Metric panels */
    .metric-card {
        background-color: #1E293B;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: white;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94A3B8;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. Session State Initialization
# -------------------------------------------------------------
if "audit_status" not in st.session_state:
    st.session_state["audit_status"] = "IDLE"
if "audit_stage" not in st.session_state:
    st.session_state["audit_stage"] = 0
if "audit_progress_text" not in st.session_state:
    st.session_state["audit_progress_text"] = ""
if "audit_partial_data" not in st.session_state:
    st.session_state["audit_partial_data"] = {}
if "liquid_assets" not in st.session_state:
    st.session_state["liquid_assets"] = 0.0
if "total_assets" not in st.session_state:
    st.session_state["total_assets"] = 0.0
if "total_liabilities" not in st.session_state:
    st.session_state["total_liabilities"] = 0.0
if "overrides" not in st.session_state:
    db_overrides = get_all_overrides()
    st.session_state["overrides"] = db_overrides if db_overrides else {}
if "raw_txs" not in st.session_state:
    st.session_state["raw_txs"] = []
if "audit_completed" not in st.session_state:
    st.session_state["audit_completed"] = False
if "state" not in st.session_state:
    st.session_state["state"] = None
if "report_md" not in st.session_state:
    st.session_state["report_md"] = ""
if "last_run_params" not in st.session_state:
    st.session_state["last_run_params"] = None

# -------------------------------------------------------------
# 5. Sidebar Inputs
# -------------------------------------------------------------
st.sidebar.markdown("### 🔑 Configuration")
api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    help="Leave blank to run in 'mock' mode for local unit-testing.",
    placeholder="Enter API Key or leave blank for mock"
)
# Default to mock mode if key is empty
if not api_key:
    api_key = "mock"

# Base Currency Selectbox
st.sidebar.markdown("### 💱 Currency Selection")
currency_option = st.sidebar.selectbox(
    "Base Currency",
    options=["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "AED (د.إ)", "CNY (¥)", "Other"],
    index=0,
    help="Select the currency for your inputs and reports."
)

if currency_option == "Other":
    selected_symbol = "$"
    selected_name = "Other"
else:
    import re
    symbol_match = re.search(r'\((.*?)\)', currency_option)
    selected_symbol = symbol_match.group(1) if symbol_match else "$"
    selected_name = currency_option.split(" ")[0]

st.sidebar.markdown("### 📊 Balance Sheet Details")
liquid_assets = st.sidebar.number_input(
    f"Liquid Cash / Savings ({selected_symbol})",
    min_value=0.0,
    value=st.session_state["liquid_assets"],
    step=500.0,
    help="Total cash held in checkings/savings."
)
st.session_state["liquid_assets"] = liquid_assets

total_assets = st.sidebar.number_input(
    f"Total Assets ({selected_symbol})",
    min_value=0.0,
    value=st.session_state["total_assets"],
    step=500.0,
    help="Total property, cash, and investments."
)
st.session_state["total_assets"] = total_assets

total_liabilities = st.sidebar.number_input(
    f"Total Liabilities ({selected_symbol})",
    min_value=0.0,
    value=st.session_state["total_liabilities"],
    step=500.0,
    help="Total outstanding debt balances."
)
st.session_state["total_liabilities"] = total_liabilities

# -------------------------------------------------------------
# 6. Main Hero Banner
# -------------------------------------------------------------
st.markdown("""
<div class="header-container">
    <h1 class="header-title">CashFlow AI</h1>
    <p class="header-subtitle">AI-Powered Financial Intelligence Coach & Behavioral Risk Diagnostician</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 7. File Upload & Inferred Metrics Pre-population
# -------------------------------------------------------------
st.markdown("### 📂 Upload Financial Statement")
uploaded_file = st.file_uploader(
    "Upload bank transaction records (CSV format)",
    type=["csv"],
    help="Standard CSV files containing Date, Description, and Amount."
)

if uploaded_file is not None:
    # Auto-infer balance sheet figures when file is dropped
    file_key = f"parsed_{uploaded_file.name}_{uploaded_file.size}"
    if file_key not in st.session_state:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name
            
            try:
                inferred = extract_balances_from_csv(temp_file_path)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
            if inferred:
                st.session_state["liquid_assets"] = inferred["liquid_assets"]
                st.session_state["total_assets"] = inferred["total_assets"]
                st.session_state["total_liabilities"] = inferred["total_liabilities"]
                st.session_state[file_key] = True
                st.toast("💡 Inferred balance sheet metrics from statement accounts!")
                st.rerun()
        except Exception as e:
            st.error(f"Error parsing balance sheet info: {e}")


    # Hide the run button if audit is running
    if st.session_state["audit_status"] == "IDLE" or st.session_state["audit_status"] == "COMPLETED" or st.session_state["audit_status"] == "CANCELLED" or st.session_state["audit_status"] == "FAILED":
        run_btn = st.button("Run Financial Audit", type="primary")
        
        if run_btn:
            # Initialize State Machine
            st.session_state["audit_status"] = "RUNNING"
            st.session_state["audit_stage"] = 0
            st.session_state["audit_progress_text"] = "Parsing CSV and loading transactions..."
            st.session_state["audit_partial_data"] = {}
            st.session_state["audit_completed"] = False
            
            # Save uploaded buffer to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # Ingest and parse CSV transactions
                raw_txs = parse_csv_to_models(temp_file_path)
                
                # Clean and deduplicate transactions
                raw_txs = clean_transactions(raw_txs)
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
            if not raw_txs:
                st.error("No valid transactions found in the uploaded statement.")
                st.session_state["audit_status"] = "FAILED"
            else:
                st.session_state["raw_txs"] = raw_txs
                st.rerun()
                
    # --- Progress UI and State Machine Execution ---
    if st.session_state["audit_status"] in ["RUNNING", "CANCELLING"]:
        st.markdown("### ⏳ Audit in Progress...")
        col1, col2 = st.columns([3, 1])
        with col1:
            progress_fraction = st.session_state["audit_stage"] / 5.0
            if progress_fraction > 1.0: progress_fraction = 1.0
            
            import time
            progress_text = st.session_state["audit_progress_text"]
            if "start_time" in st.session_state.get("audit_partial_data", {}):
                elapsed = time.perf_counter() - st.session_state["audit_partial_data"]["start_time"]
                progress_text = f"{progress_text} (Elapsed: {elapsed:.1f}s)"
                
            st.progress(progress_fraction, text=progress_text)
        with col2:
            if st.session_state["audit_status"] == "RUNNING":
                if st.button("🛑 Stop Audit", type="secondary"):
                    st.session_state["audit_status"] = "CANCELLING"
                    st.rerun()
            else:
                st.button("Stopping...", type="secondary", disabled=True)

        # Execute exactly one stage
        try:
            stage = st.session_state["audit_stage"]
            if stage == 0:
                import time
                st.session_state["audit_partial_data"]["start_time"] = time.perf_counter()
                
                # Initialize state dictionary
                state = StateDict()
                state.raw_data["currency_symbol"] = selected_symbol
                state.raw_data["currency_name"] = selected_name
                state.user_memory["overrides"] = st.session_state["overrides"]
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 1
                st.session_state["audit_progress_text"] = "Stage 1: Deterministic Transaction Understanding..."
                st.rerun()
                
            elif stage == 1:
                state = st.session_state["audit_partial_data"]["state"]
                raw_txs = st.session_state["raw_txs"]
                
                first_pass_txs = []
                unknown_tx_map = {}
                
                for tx in raw_txs:
                    ptx = process_transaction(tx, overrides_dict=state.user_memory.get("overrides", {}))
                    if ptx.confidence_score <= 0.0:
                        unknown_tx_map[ptx.raw_description] = {
                            "description": ptx.raw_description, 
                            "amount": ptx.amount,
                            "csv_type": tx.csv_type,
                            "csv_category": tx.csv_category
                        }
                    first_pass_txs.append(ptx)
                    
                st.session_state["audit_partial_data"]["first_pass_txs"] = first_pass_txs
                
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_partial_data"]["ai_mappings"] = {}
                    st.session_state["audit_stage"] = 6
                    st.rerun()
                
                unknown_list = list(unknown_tx_map.values())
                chunk_size = 50
                chunks = [unknown_list[i:i + chunk_size] for i in range(0, len(unknown_list), chunk_size)]
                
                st.session_state["audit_partial_data"]["ai_chunks"] = chunks
                st.session_state["audit_partial_data"]["current_chunk_idx"] = 0
                st.session_state["audit_partial_data"]["ai_mappings"] = {}
                
                if chunks:
                    st.session_state["audit_stage"] = 2.1
                    st.session_state["audit_progress_text"] = f"Stage 2: AI Categorization (Chunk 1 of {len(chunks)})..."
                else:
                    st.session_state["audit_stage"] = 2.2
                    st.session_state["audit_progress_text"] = "Stage 2: Applying Mappings..."
                st.rerun()
                
            elif stage == 2.1:
                chunks = st.session_state["audit_partial_data"]["ai_chunks"]
                
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_stage"] = 6
                    st.rerun()
                
                if api_key and api_key != "mock":
                    from skills.transaction_understanding.ai import batch_classify_transactions
                    import time
                    
                    all_mappings = {}
                    progress_placeholder = st.empty()
                    
                    for i, chunk in enumerate(chunks):
                        progress_placeholder.info(f"🧠 AI Categorization: Processing chunk {i+1} of {len(chunks)}...")
                        try:
                            chunk_mappings, chunk_usage = batch_classify_transactions(chunk, api_key)
                            all_mappings.update(chunk_mappings)
                            
                            prompt_per_tx = chunk_usage.get("promptTokenCount", 0) // len(chunk) if chunk else 0
                            cand_per_tx = chunk_usage.get("candidatesTokenCount", 0) // len(chunk) if chunk else 0
                            
                            if "ai_usage" not in st.session_state["audit_partial_data"]:
                                st.session_state["audit_partial_data"]["ai_usage"] = {}
                                
                            for desc in chunk_mappings.keys():
                                st.session_state["audit_partial_data"]["ai_usage"][desc] = {
                                    "prompt_tokens": prompt_per_tx,
                                    "candidates_tokens": cand_per_tx
                                }
                            if i < len(chunks) - 1:
                                time.sleep(4)
                        except Exception as e:
                            import streamlit as st
                            st.toast(f"⚠️ AI Categorization Failed on chunk {i+1}: {e}. Proceeding with what we have.")
                            
                    progress_placeholder.empty()
                    st.session_state["audit_partial_data"]["ai_mappings"].update(all_mappings)
                
                st.session_state["audit_stage"] = 2.2
                st.rerun()

            elif stage == 2.2:
                state = st.session_state["audit_partial_data"]["state"]
                first_pass_txs = st.session_state["audit_partial_data"]["first_pass_txs"]
                ai_mappings = st.session_state["audit_partial_data"]["ai_mappings"]
                
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
                        if "associated_person" in ai_data and ai_data["associated_person"]:
                            ptx.associated_person = ai_data["associated_person"]
                        from skills.transaction_understanding.rules import derive_intent_and_impact
                        ptx.intent, ptx.financial_impact = derive_intent_and_impact(ptx.category, ptx.sub_category)
                        ptx.confidence_score = 0.8
                        ptx.classification_method = "ai_fallback"
                        
                        usage = st.session_state["audit_partial_data"].get("ai_usage", {}).get(ptx.raw_description, {})
                        ptx.prompt_tokens = usage.get("prompt_tokens", 0)
                        ptx.candidates_tokens = usage.get("candidates_tokens", 0)
                    final_transactions.append(ptx)
                    
                state.processed_data["transactions"] = final_transactions
                st.session_state["audit_partial_data"]["state"] = state
                
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_stage"] = 6
                    st.rerun()
                
                st.session_state["audit_stage"] = 3
                st.session_state["audit_progress_text"] = "Stage 3: Running Financial Analysis & Ratios..."
                st.rerun()
                
            elif stage == 3:
                state = st.session_state["audit_partial_data"]["state"]
                raw_txs = st.session_state["raw_txs"]
                
                state = run_financial_analysis(
                    state=state,
                    liquid_assets=liquid_assets,
                    total_assets=total_assets,
                    total_liabilities=total_liabilities
                )
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 4
                st.session_state["audit_progress_text"] = "Stage 4: Running Behavioral Risk Analysis..."
                st.rerun()
                
            elif stage == 4:
                state = st.session_state["audit_partial_data"]["state"]
                state = run_behavior_analysis(state)
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 5
                st.session_state["audit_progress_text"] = "Stage 5: Finalizing Report with AI Financial Coach..."
                st.rerun()
                
            elif stage == 5:
                import time
                state = st.session_state["audit_partial_data"]["state"]
                
                try:
                    state = run_financial_coach(state, api_key=api_key)
                except Exception as e:
                    import streamlit as st
                    st.toast(f"⚠️ AI Coach Failed: {e}. Generating deterministic report instead.")
                    
                try:
                    report_md = run_report_generation(state)
                except Exception as e:
                    import traceback
                    report_md = f"### ⚠️ Report Generation Failed\n\n**Error:** `{e}`\n\n```python\n{traceback.format_exc()}\n```"
                
                end_time = time.perf_counter()
                exec_time = end_time - st.session_state["audit_partial_data"]["start_time"]
                
                final_transactions = state.processed_data["transactions"]
                fallback_in_tokens = sum(tx.prompt_tokens for tx in final_transactions if hasattr(tx, "prompt_tokens") and tx.prompt_tokens)
                fallback_out_tokens = sum(tx.candidates_tokens for tx in final_transactions if hasattr(tx, "candidates_tokens") and tx.candidates_tokens)
                
                coach_in_tokens = state.agent_outputs.get("promptTokenCount", 0)
                coach_out_tokens = state.agent_outputs.get("candidatesTokenCount", 0)
                
                total_in = fallback_in_tokens + coach_in_tokens
                total_out = fallback_out_tokens + coach_out_tokens
                
                estimated_cost = (total_in * 0.075 / 1_000_000) + (total_out * 0.30 / 1_000_000)
                
                state.processed_data["telemetry"] = {
                    "execution_time_sec": round(exec_time, 4),
                    "total_input_tokens": total_in,
                    "total_output_tokens": total_out,
                    "estimated_cost_usd": round(estimated_cost, 6)
                }
                
                st.session_state["state"] = state
                st.session_state["report_md"] = report_md
                st.session_state["audit_completed"] = True
                
                was_cancelled = st.session_state["audit_status"] == "CANCELLING"
                st.session_state["audit_status"] = "CANCELLED" if was_cancelled else "COMPLETED"
                
                st.session_state["last_run_params"] = {
                    "liquid": liquid_assets,
                    "assets": total_assets,
                    "liabilities": total_liabilities,
                    "api_key": api_key,
                    "currency_symbol": selected_symbol
                }
                calculated_income = state.processed_data["ratios"].get("total_absolute_income", state.processed_data["ratios"].get("monthly_income", 0.0))
                if was_cancelled:
                    st.warning(f"⚠️ Audit Cancelled gracefully. Partial results loaded.")
                else:
                    st.success(f"✅ Audit Completed! Detected Absolute Income: {selected_symbol}{calculated_income:,.2f}")
                st.rerun()

            elif stage == 6:
                import time
                end_time = time.perf_counter()
                exec_time = end_time - st.session_state["audit_partial_data"]["start_time"]
                
                state = st.session_state["audit_partial_data"]["state"]
                state.processed_data["telemetry"] = {
                    "execution_time_sec": round(exec_time, 4),
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "estimated_cost_usd": 0.0
                }
                st.session_state["state"] = state
                st.session_state["report_md"] = "### ⚠️ Audit Cancelled gracefully.\n\nNo report generated."
                st.session_state["audit_completed"] = True
                st.session_state["audit_status"] = "CANCELLED"
                st.session_state["last_run_params"] = {
                    "liquid": liquid_assets,
                    "assets": total_assets,
                    "liabilities": total_liabilities,
                    "api_key": api_key,
                    "currency_symbol": selected_symbol
                }
                st.warning(f"⚠️ Audit Cancelled cleanly after {exec_time:.1f}s.")
                st.rerun()

        except Exception as e:
            from streamlit.runtime.scriptrunner import RerunException
            if isinstance(e, RerunException):
                raise e
            st.session_state["audit_status"] = "FAILED"
            st.error(f"Error during pipeline execution at Stage {st.session_state['audit_stage']}: {e}")
            st.stop()


# -------------------------------------------------------------
# 8. Reactive Rerun on Sidebar Parameter Change
# -------------------------------------------------------------
if st.session_state.get("audit_completed") and st.session_state.get("raw_txs"):
    current_params = {
        "liquid": liquid_assets,
        "assets": total_assets,
        "liabilities": total_liabilities,
        "api_key": api_key,
        "currency_symbol": selected_symbol
    }
    if st.session_state.get("last_run_params") != current_params:
        if st.session_state["audit_status"] == "IDLE":
            st.toast("Parameters changed. Restarting audit...")
            st.session_state["audit_status"] = "RUNNING"
            st.session_state["audit_stage"] = 0
            st.session_state["audit_progress_text"] = "Parsing CSV and loading transactions..."
            st.session_state["audit_partial_data"] = {}
            st.session_state["audit_completed"] = False
            st.rerun()

# -------------------------------------------------------------
# 8.5 Ledger Override Re-Run
# -------------------------------------------------------------
# Handled in the Dashboard section.

# 9. Dashboard & Ledger Presentation
# -------------------------------------------------------------
if st.session_state["audit_completed"]:
    state = st.session_state["state"]
    report_md = st.session_state["report_md"]
    
    score = state.processed_data["financial_health_score"]
    ratios = state.processed_data["ratios"]
    behavior = state.processed_data["behavior"]
    quick_wins = state.agent_outputs.get("quick_wins", [])
    roadmap = state.agent_outputs.get("roadmap", "")
    
    # Tier mapping color coding
    if score >= 85.0:
        badge_color = "#10B981"  # Emerald
        tier_label = "Excellent"
    elif score >= 70.0:
        badge_color = "#3B82F6"  # Blue
        tier_label = "Good"
    elif score >= 50.0:
        badge_color = "#F59E0B"  # Amber
        tier_label = "Fair"
    else:
        badge_color = "#EF4444"  # Red
        tier_label = "Needs Attention"
        
    if not api_key or api_key == "mock":
        st.warning("⚠️ Using Mock API. AI advice is placeholder. Enter a Gemini Key for real analysis.")
        
    st.markdown("---")
    
    # 9.1. Metric Scorecard Header
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""
        <div style="background-color: {badge_color}; padding: 1.5rem; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.9;">Health Score</div>
            <div style="font-size: 3.5rem; font-weight: 800; margin: 0.25rem 0;">{score:.1f}</div>
            <div style="font-size: 1.1rem; font-weight: 500; opacity: 0.95;">{tier_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("#### Audit Ratios Summary")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        # Savings Rate Card
        with m_col1:
            sav_rate = ratios.get("savings_rate", 0.0) * 100.0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Monthly Savings</div>
                <div class="metric-value" style="color: {'#10B981' if sav_rate >= 20.0 else '#EF4444'}">{sav_rate:.1f}%</div>
                <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #94A3B8;">Target: Save >= 20%</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Debt Ratio Card
        with m_col2:
            debt_rate = ratios.get("debt_ratio", 0.0) * 100.0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Debt Burden</div>
                <div class="metric-value" style="color: {'#10B981' if debt_rate <= 15.0 else '#EF4444'}">{debt_rate:.1f}%</div>
                <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #94A3B8;">Target: Keep <= 15%</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Runway Card
        with m_col3:
            runway_val = ratios.get("emergency_runway_months", 0.0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Emergency Fund</div>
                <div class="metric-value" style="color: {'#10B981' if runway_val >= 6.0 else '#EF4444'}">{runway_val:.1f} mo</div>
                <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #94A3B8;">Target: >= 6.0 months</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col4:
            coverage = ratios.get("asset_coverage", 999.0)
            cov_val = f"{coverage:.2f}x" if coverage < 999.0 else "No Debt!"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Safety Net</div>
                <div class="metric-value" style="color: {'#10B981' if coverage >= 3.0 or coverage >= 999.0 else '#EF4444'}">{cov_val}</div>
                <div style="font-size: 0.8rem; margin-top: 0.25rem; color: #94A3B8;">Target: Assets >= 3x Debt</div>
            </div>
            """, unsafe_allow_html=True)

    # Tabs for separation of concerns
    tab_dashboard, tab_ledger, tab_report = st.tabs(["📊 Financial Dashboard", "✏️ Interactive Transaction Ledger", "📄 Financial Report"])
    
    with tab_dashboard:
        # Spending Behavior Audit section
        st.markdown("### 🔍 Spending Insights")
        
        chart_col, ts_col = st.columns(2)
        
        # Render Altair category concentration chart
        with chart_col:
            concentrations = behavior.get("category_concentration", [])
            if concentrations:
                df_chart = pd.DataFrame(concentrations)
                
                # Custom styled horizontal bar chart
                chart = alt.Chart(df_chart).mark_bar(
                    cornerRadiusTopRight=6,
                    cornerRadiusBottomRight=6,
                    height=30
                ).encode(
                    x=alt.X("percentage:Q", title="Percentage of Spend (%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("category:N", title="Budget Category", sort="-x"),
                    color=alt.Color(
                        "category:N", 
                        scale=alt.Scale(scheme="category20b"),
                        legend=None
                    )
                ).properties(
                    title="Expense Category Concentrations",
                    height=200
                ).configure_title(
                    fontSize=14,
                    font="Inter",
                    anchor="start"
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No expense categories found to chart.")
                
        # Render Cumulative Spending line chart
        with ts_col:
            expense_txs = [tx for tx in state.processed_data["transactions"] if tx.transaction_type == "Expense"]
            if expense_txs:
                # Sort by date
                expense_txs = sorted(expense_txs, key=lambda x: x.date)
                
                # Group by date and sum amount
                daily_totals = {}
                for tx in expense_txs:
                    d_str = tx.date.strftime("%Y-%m-%d")
                    daily_totals[d_str] = daily_totals.get(d_str, 0.0) + abs(tx.amount)
                    
                # Convert to DataFrame
                df_ts = pd.DataFrame([{"Date": k, "Daily Spend": v} for k, v in daily_totals.items()])
                df_ts = df_ts.sort_values(by="Date")
                
                # Cumulative spend
                df_ts["Cumulative Spend"] = df_ts["Daily Spend"].cumsum()
                
                # Plot cumulative spend line chart
                ts_chart = alt.Chart(df_ts).mark_line(
                    color="#6366F1",
                    strokeWidth=3,
                    point=alt.OverlayMarkDef(color="#4F46E5", size=50)
                ).encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y("Cumulative Spend:Q", title="Total Cumulative Expenses ($)"),
                    tooltip=["Date:T", "Daily Spend:Q", "Cumulative Spend:Q"]
                ).properties(
                    title="Cumulative Expenses Over Time",
                    height=200
                ).configure_title(
                    fontSize=14,
                    font="Inter",
                    anchor="start"
                )
                st.altair_chart(ts_chart, use_container_width=True)
            else:
                st.info("No expenses found to chart over time.")
                
        # Risk Indicators panel
        st.markdown("#### Important Notices")
        risks = behavior.get("potential_risk_indicators", [])
        if risks:
            for risk in risks:
                st.warning(risk)
        else:
            st.success("✓ No major issues detected.")
            
        st.subheader("Weekly Spending Breakdown")
        weekly_spending = behavior.get("weekly_spending", [])
        if weekly_spending:
            weekly_spending_df = pd.DataFrame(weekly_spending)
            w_col1, w_col2 = st.columns([1, 2])
            with w_col1:
                st.table(weekly_spending_df)
            with w_col2:
                weekly_chart = alt.Chart(weekly_spending_df).mark_bar(
                    color="#6366F1",
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4
                ).encode(
                    x=alt.X('week_number:O', title='Week Number'),
                    y=alt.Y('total_spent:Q')
                ).properties(
                    height=200
                )
                st.altair_chart(weekly_chart, use_container_width=True)
        else:
            st.info("No weekly spending data available.")
                 
        st.markdown("---")
        
        # AI Coach Recommendations
        st.markdown("### 🤖 Financial Coach Recommendations")
        
        # Render Quick Wins side-by-side
        st.markdown("#### Actionable Quick Wins")
        if quick_wins:
            w_col1, w_col2, w_col3 = st.columns(3)
            cols = [w_col1, w_col2, w_col3]
            for idx, win in enumerate(quick_wins):
                title = win.get("title", f"Quick Win {idx+1}")
                desc = win.get("description", "")
                savings = win.get("potential_savings", 0)
                curr_sym = state.raw_data.get("currency_symbol", "$")
                
                try:
                    savings_val = float(str(savings).replace(curr_sym, "").replace("$", "").replace(",", ""))
                except ValueError:
                    savings_val = 0
                    
                savings_str = f"{curr_sym}{savings_val:,.0f}/mo" if savings_val > 0 else str(savings) if savings else "N/A"
                
                with cols[idx % 3]:
                    st.info(f"""
                    **{title}**  
                    {desc}  
                    *Potential Monthly Savings: **{savings_str}***
                    """)
        else:
            st.info("No quick wins generated.")
            
        # Render long-term roadmap
        st.markdown("#### Goal Roadmap")
        if roadmap:
            st.markdown(roadmap)
        else:
            st.info("No goal roadmap generated.")
            
        st.markdown("---")
        
        # Download Report Section
        st.markdown("### 💾 Export Audit Report")
        st.download_button(
            label="Download Financial Audit Report (.md)",
            data=report_md,
            file_name="CashFlow_Audit_Report.md",
            mime="text/markdown",
            help="Download the compiled calculations and AI coaching roadmap as a markdown file."
        )

    with tab_ledger:
        st.markdown("### ✍️ Transaction Categorization Editor")
        st.markdown("""
        Below is the ledger of categorized transactions. If you correct any `category` in the table below, the system will:
        1. Remember this override for all matching transactions.
        2. Automatically re-categorize other matching items.
        3. Recalculate your Financial Health Score, spending concentrations, and AI recommendations.
        """)
        
        # Convert processed transactions to a DataFrame for editing
        txs_list = state.processed_data["transactions"]
        df_data = []
        for tx in txs_list:
            df_data.append({
                "Date": tx.date,
                "Raw Description": tx.raw_description,
                "Amount": tx.amount,
                "Clean Merchant": tx.clean_merchant,
                "Type": tx.transaction_type,
                "Category": tx.category,
                "Sub-Category": tx.sub_category,
                "Intent": getattr(tx, "intent", "Uncategorized"),
                "Financial Impact": getattr(tx, "financial_impact", "Uncategorized"),
                "Validation Reason": getattr(tx, "classification_reason", "Passed validation"),
                "Method": "🤖 AI Suggested" if tx.classification_method == "ai_fallback" else tx.classification_method
            })
        df = pd.DataFrame(df_data)

        # Let user edit the category column
        edited_df = st.data_editor(
            df,
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Assign correct category to this transaction",
                    options=["Food", "Shopping", "Medical", "Housing", "Transport", "Entertainment", "Investment", "Income", "Transfer", "Loan/Debt", "Other"],
                    required=True
                ),
                "Sub-Category": st.column_config.TextColumn(
                    "Sub-Category"
                )
            },
            disabled=["Date", "Raw Description", "Amount", "Clean Merchant", "Type", "Intent", "Financial Impact", "Validation Reason", "Method"],
            use_container_width=True,
            key="ledger_editor"
        )
        
        # Detect category changes in the editor
        has_changes = False
        for idx, row in edited_df.iterrows():
            old_cat = df.at[idx, "Category"]
            new_cat = row["Category"]
            old_sub = df.at[idx, "Sub-Category"]
            new_sub = row["Sub-Category"]
            
            if old_cat != new_cat or old_sub != new_sub:
                has_changes = True
                from skills.data_cleaning.cleaner import clean_transaction_description
                raw_desc = row["Raw Description"]
                clean_desc = clean_transaction_description(raw_desc)
                
                # Save mapping to overrides dict and database
                st.session_state["overrides"][clean_desc] = {
                    "merchant_name": row["Clean Merchant"],
                    "transaction_type": row["Type"],
                    "category": new_cat,
                    "sub_category": new_sub
                }
                upsert_override(clean_desc, row["Clean Merchant"], row["Type"], new_cat, new_sub)
                
        if has_changes:
            st.toast("⚡ Categories updated! Restarting analysis...")
            st.session_state["audit_status"] = "RUNNING"
            st.session_state["audit_stage"] = 0
            st.session_state["audit_progress_text"] = "Applying overrides..."
            st.session_state["audit_partial_data"] = {}
            st.session_state["audit_completed"] = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 💾 Export Ledger Data")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Categorized Ledger (.csv)",
            data=csv_data,
            file_name="CashFlow_Ledger_Export.csv",
            mime="text/csv",
            help="Download all processed transactions as a CSV file for your own spreadsheet."
        )

    with tab_report:
        st.markdown("### 📄 Final Financial Report")
        st.markdown(report_md)

    # 9.3. System Telemetry & Cost Dashboard Section
    st.markdown("---")
    st.markdown("### ⏱️ System Telemetry & Cost")
    
    telemetry = state.processed_data.get("telemetry", {
        "execution_time_sec": 0.0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "estimated_cost_usd": 0.0
    })
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.metric(
            label="Execution Time",
            value=f"{telemetry.get('execution_time_sec', 0.0):.3f}s",
            help="Total execution duration of the ingestion, analysis, behavior parsing, and coaching pipeline."
        )
    with t_col2:
        st.metric(
            label="Total Input Tokens",
            value=f"{telemetry.get('total_input_tokens', 0):,}",
            help="Total input tokens sent to the Gemini 2.5 Flash API."
        )
    with t_col3:
        st.metric(
            label="Total Output Tokens",
            value=f"{telemetry.get('total_output_tokens', 0):,}",
            help="Total output tokens generated by the Gemini 2.5 Flash API."
        )
    with t_col4:
        st.metric(
            label="Estimated API Cost",
            value=f"${telemetry.get('estimated_cost_usd', 0.0):.6f}",
            help="Calculated using Gemini 2.5 Flash pricing: $0.075/1M input tokens and $0.30/1M output tokens."
        )
