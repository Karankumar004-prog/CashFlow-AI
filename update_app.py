import sys

def update():
    with open("app.py", "r") as f:
        lines = f.readlines()
        
    # We want to add imports after line 26:
    # "from skills.reporting_layer.pipeline import run_report_generation\n"
    import_idx = -1
    for i, line in enumerate(lines):
        if "from skills.reporting_layer.pipeline import run_report_generation" in line:
            import_idx = i
            break
            
    if import_idx != -1:
        lines.insert(import_idx + 1, "from skills.data_ingestion.balance_inference import extract_balances_from_csv\n")
        lines.insert(import_idx + 2, "from skills.core.orchestrator import run_pipeline\n")
        
    # Now we want to delete the function definitions.
    # We look for "# 2. Balance Sheet Extraction Helper"
    start_del = -1
    end_del = -1
    for i, line in enumerate(lines):
        if "# 2. Balance Sheet Extraction Helper" in line:
            start_del = i - 1 # include the top border
        if "# 4. Session State Initialization" in line:
            end_del = i - 1 # up to the top border of section 4
            break
            
    if start_del != -1 and end_del != -1:
        del lines[start_del:end_del]
        
    with open("app.py", "w") as f:
        f.writelines(lines)

update()
print("app.py updated successfully")
