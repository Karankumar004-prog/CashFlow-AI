with open("app.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == "if has_changes:" and "st.toast" in lines[i+1]:
        new_lines.append("        if has_changes:\n")
        new_lines.append("            st.toast(\"⚡ Categories updated! Restarting analysis...\")\n")
        new_lines.append("            st.session_state[\"audit_status\"] = \"RUNNING\"\n")
        new_lines.append("            st.session_state[\"audit_stage\"] = 0\n")
        new_lines.append("            st.session_state[\"audit_progress_text\"] = \"Applying overrides...\"\n")
        new_lines.append("            st.session_state[\"audit_partial_data\"] = {}\n")
        new_lines.append("            st.session_state[\"audit_completed\"] = False\n")
        new_lines.append("            st.rerun()\n")
        skip = True
    elif skip and "st.rerun()" in line:
        skip = False
    elif not skip:
        new_lines.append(line)

with open("app.py", "w") as f:
    f.writelines(new_lines)
