import sys

def patch():
    with open("app.py", "r") as f:
        content = f.read()
        
    old_call = """                            chunk_mappings = batch_classify_transactions(chunk, api_key)
                            all_mappings.update(chunk_mappings)"""
                            
    new_call = """                            chunk_mappings, chunk_usage = batch_classify_transactions(chunk, api_key)
                            all_mappings.update(chunk_mappings)
                            
                            prompt_per_tx = chunk_usage.get("promptTokenCount", 0) // len(chunk) if chunk else 0
                            cand_per_tx = chunk_usage.get("candidatesTokenCount", 0) // len(chunk) if chunk else 0
                            
                            if "ai_usage" not in st.session_state["audit_partial_data"]:
                                st.session_state["audit_partial_data"]["ai_usage"] = {}
                                
                            for desc in chunk_mappings.keys():
                                st.session_state["audit_partial_data"]["ai_usage"][desc] = {
                                    "prompt_tokens": prompt_per_tx,
                                    "candidates_tokens": cand_per_tx
                                }"""
                                
    old_assign = """                        ptx.confidence_score = 0.8
                        ptx.classification_method = "ai_fallback"
                    final_transactions.append(ptx)"""
                    
    new_assign = """                        ptx.confidence_score = 0.8
                        ptx.classification_method = "ai_fallback"
                        
                        usage = st.session_state["audit_partial_data"].get("ai_usage", {}).get(ptx.raw_description, {})
                        ptx.prompt_tokens = usage.get("prompt_tokens", 0)
                        ptx.candidates_tokens = usage.get("candidates_tokens", 0)
                    final_transactions.append(ptx)"""
                    
    if old_call in content and old_assign in content:
        content = content.replace(old_call, new_call)
        content = content.replace(old_assign, new_assign)
        
        with open("app.py", "w") as f:
            f.write(content)
        print("Patched app.py successfully!")
    else:
        print("Could not find the target strings in app.py")
        
patch()
