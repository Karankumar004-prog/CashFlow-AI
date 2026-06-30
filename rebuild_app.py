import sys

def rebuild():
    with open("app.py", "r") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    
    # Find "if run_btn:"
    for i, line in enumerate(lines):
        if "if run_btn:" in line:
            start_idx = i
            break
            
    # Find the end of the block
    for i in range(start_idx, len(lines)):
        if "# -------------------------------------------------------------" in lines[i]:
            end_idx = i
            break
            
    if start_idx == -1 or end_idx == -1:
        print(f"Could not find boundaries: start={start_idx}, end={end_idx}")
        return
        
    new_code = """        if run_btn:
            st.session_state["audit_status"] = "RUNNING"
            st.session_state["audit_stage"] = 0
            st.session_state["audit_progress_text"] = "Parsing CSV and loading transactions..."
            st.session_state["audit_partial_data"] = {}
            st.session_state["audit_completed"] = False
            
            import tempfile
            import os
            cache_obj = st.session_state[csv_cache_key]
            with tempfile.NamedTemporaryFile(delete=False, suffix=cache_obj["ext"], mode='wb') as temp_file:
                temp_file.write(cache_obj["data"])
                temp_file_path = temp_file.name
                
            from skills.data_ingestion.ingestion import parse_csv_to_models
            raw_txs = parse_csv_to_models(temp_file_path)
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            if not raw_txs:
                st.error("No valid transactions found in the uploaded statement.")
                st.session_state["audit_status"] = "FAILED"
            else:
                st.session_state["raw_txs"] = raw_txs
                st.rerun()
                
    # --- Progress UI and State Machine Execution ---
    if st.session_state.get("audit_status") in ["RUNNING", "CANCELLING"]:
        st.markdown("### ⏳ Audit in Progress...")
        col1, col2 = st.columns([3, 1])
        with col1:
            progress_fraction = st.session_state.get("audit_stage", 0) / 5.0
            if progress_fraction > 1.0: progress_fraction = 1.0
            st.progress(progress_fraction, text=st.session_state.get("audit_progress_text", "Processing..."))
        with col2:
            if st.session_state["audit_status"] == "RUNNING":
                if st.button("🛑 Stop Audit", type="secondary"):
                    st.session_state["audit_status"] = "CANCELLING"
                    st.rerun()
            else:
                st.button("Stopping...", type="secondary", disabled=True)

        try:
            stage = st.session_state["audit_stage"]
            if stage == 0:
                import time
                from skills.core.models import StateDict
                st.session_state["audit_partial_data"]["start_time"] = time.perf_counter()
                
                state = StateDict()
                state.raw_data["currency_symbol"] = selected_symbol
                state.raw_data["currency_name"] = selected_name
                state.user_memory["overrides"] = st.session_state.get("overrides", {})
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 1
                st.session_state["audit_progress_text"] = "Stage 1: Deterministic Transaction Understanding..."
                st.rerun()
                
            elif stage == 1:
                from skills.transaction_understanding.pipeline import process_transaction
                state = st.session_state["audit_partial_data"]["state"]
                raw_txs = st.session_state["raw_txs"]
                
                first_pass_txs = []
                unknown_descriptions = set()
                
                for tx in raw_txs:
                    ptx = process_transaction(tx, overrides_dict=state.user_memory.get("overrides", {}))
                    if ptx.confidence_score <= 0.0:
                        unknown_descriptions.add(ptx.raw_description)
                    first_pass_txs.append(ptx)
                    
                st.session_state["audit_partial_data"]["first_pass_txs"] = first_pass_txs
                
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_partial_data"]["ai_mappings"] = {}
                    st.session_state["audit_stage"] = 2.2
                    st.rerun()
                
                unknown_list = list(unknown_descriptions)
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
                    st.session_state["audit_progress_text"] = "Stage 2: Applying Deterministic Mappings..."
                st.rerun()
                
            elif stage == 2.1:
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_stage"] = 2.2
                    st.rerun()
                    
                chunks = st.session_state["audit_partial_data"]["ai_chunks"]
                current_idx = st.session_state["audit_partial_data"]["current_chunk_idx"]
                total_chunks = len(chunks)
                
                if current_idx < total_chunks and api_key and api_key != "mock":
                    from skills.transaction_understanding.ai import batch_classify_transactions
                    import time
                    chunk = chunks[current_idx]
                    
                    st.session_state["audit_progress_text"] = f"Stage 2: AI Categorization (Chunk {current_idx+1} of {total_chunks})..."
                    
                    try:
                        chunk_mappings = batch_classify_transactions(chunk, api_key)
                        st.session_state["audit_partial_data"]["ai_mappings"].update(chunk_mappings)
                    except Exception as e:
                        st.toast(f"⚠️ AI Categorization Failed on chunk {current_idx+1}: {e}")
                        
                    st.session_state["audit_partial_data"]["current_chunk_idx"] += 1
                    
                    # Prevent rapid-fire 429 rate limit spam for Gemini (2 seconds delay per chunk is standard)
                    time.sleep(2.0)
                    
                    # Yield control back to Streamlit to update progress and check for Stop clicks
                    st.rerun()
                else:
                    st.session_state["audit_stage"] = 2.2
                    st.session_state["audit_progress_text"] = "Stage 2: Applying Mappings..."
                    st.rerun()
                    
            elif stage == 2.2:
                state = st.session_state["audit_partial_data"]["state"]
                first_pass_txs = st.session_state["audit_partial_data"]["first_pass_txs"]
                ai_mappings = st.session_state["audit_partial_data"].get("ai_mappings", {})
                
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
                        if "complexity_note" in ai_data and ai_data["complexity_note"]:
                            ptx.complexity_note = ai_data["complexity_note"]
                        from skills.transaction_understanding.rules import derive_intent_and_impact
                        ptx.intent, ptx.financial_impact = derive_intent_and_impact(ptx.category, ptx.sub_category)
                        ptx.confidence_score = 0.8
                        ptx.classification_method = "ai_fallback"
                    final_transactions.append(ptx)
                    
                state.processed_data["transactions"] = final_transactions
                st.session_state["audit_partial_data"]["state"] = state
                
                if st.session_state["audit_status"] == "CANCELLING":
                    st.session_state["audit_stage"] = 3
                    st.rerun()
                
                st.session_state["audit_stage"] = 3
                st.session_state["audit_progress_text"] = "Stage 3: Running Financial Analysis & Ratios..."
                st.rerun()
                
            elif stage == 3:
                from skills.financial_intelligence.pipeline import run_financial_analysis
                state = st.session_state["audit_partial_data"]["state"]
                
                raw_txs = st.session_state["raw_txs"]
                if liquid_assets == 0.0:
                    dynamic_liquid_assets = raw_txs[-1].running_balance if raw_txs else 0.0
                else:
                    dynamic_liquid_assets = liquid_assets
                dynamic_total_assets = total_assets if total_assets > 0.0 else dynamic_liquid_assets
                
                state = run_financial_analysis(
                    state=state,
                    liquid_assets=dynamic_liquid_assets,
                    total_assets=dynamic_total_assets,
                    total_liabilities=total_liabilities
                )
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 4
                st.session_state["audit_progress_text"] = "Stage 4: Running Behavioral Risk Analysis..."
                st.rerun()
                
            elif stage == 4:
                from skills.financial_intelligence.behavior_pipeline import run_behavior_analysis
                state = st.session_state["audit_partial_data"]["state"]
                state = run_behavior_analysis(state)
                st.session_state["audit_partial_data"]["state"] = state
                
                st.session_state["audit_stage"] = 5
                st.session_state["audit_progress_text"] = "Stage 5: Finalizing Report with AI Financial Coach..."
                st.rerun()
                
            elif stage == 5:
                import time
                from skills.reasoning_layer.pipeline import run_financial_coach
                from skills.reporting_layer.pipeline import run_report_generation
                
                state = st.session_state["audit_partial_data"]["state"]
                
                if st.session_state["audit_status"] != "CANCELLING":
                    try:
                        state = run_financial_coach(state, api_key=api_key)
                    except Exception as e:
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
                
                calculated_income = state.processed_data.get("ratios", {}).get("total_absolute_income", state.processed_data.get("ratios", {}).get("monthly_income", 0.0))
                if was_cancelled:
                    st.warning(f"⚠️ Audit Cancelled gracefully. Partial results loaded.")
                else:
                    st.success(f"✅ Audit Completed! Detected Absolute Income: {selected_symbol}{calculated_income:,.2f}")
                st.rerun()

        except Exception as e:
            from streamlit.runtime.scriptrunner import RerunException
            if isinstance(e, RerunException):
                raise e
            import traceback
            st.session_state["audit_status"] = "FAILED"
            st.error(f"Error during pipeline execution at Stage {st.session_state.get('audit_stage', 'Unknown')}: {e}")
            st.error(traceback.format_exc())
            st.stop()
"""
    del lines[start_idx:end_idx]
    lines.insert(start_idx, new_code)
    
    # 2. Fix Reactive logic
    start_react = -1
    for i, line in enumerate(lines):
        if 'st.toast("Parameters changed. Restarting audit...")' in line:
            start_react = i - 1
            break
            
    if start_react != -1:
        end_react = start_react + 3
        react_code = """        if st.session_state["audit_status"] in ["IDLE", "COMPLETED"]:
            st.toast("Parameters changed. Restarting audit...")
            st.session_state["audit_status"] = "RUNNING"
            st.session_state["audit_stage"] = 0
            st.session_state["audit_progress_text"] = "Parsing CSV and loading transactions..."
            st.session_state["audit_partial_data"] = {}
            st.session_state["audit_completed"] = False
            st.rerun()
"""
        del lines[start_react:end_react]
        lines.insert(start_react, react_code)

    with open("app.py", "w") as f:
        f.writelines(lines)
        
rebuild()
print("State machine successfully restored to app.py")
