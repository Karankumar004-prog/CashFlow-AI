import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Pipeline signature
content = content.replace(
    'def run_pipeline(raw_txs, overrides, api_key, monthly_income, liquid_assets, total_assets, total_liabilities, currency_symbol="$", currency_name="USD"):',
    'def run_pipeline(raw_txs, overrides, api_key, liquid_assets, total_assets, total_liabilities, currency_symbol="$", currency_name="USD"):'
)

content = content.replace(
    '    state.raw_data["monthly_income"] = monthly_income\n',
    ''
)

# 2. Session state init
content = content.replace(
    'if "user_income_input" not in st.session_state:\n    st.session_state["user_income_input"] = 0.0\n',
    ''
)

# 3. Sidebar UI
content = re.sub(
    r'user_income_input = st\.sidebar\.number_input\([^)]*\)\n*st\.session_state\["user_income_input"\] = user_income_input\n*',
    '',
    content
)

# 4. Pipeline call arguments and last_run_params
content = content.replace('monthly_income=user_income_input,\n', '')
content = content.replace('                        "income": user_income_input,\n', '')
content = content.replace('        "income": user_income_input,\n', '')
content = content.replace('                    "income": user_income_input,\n', '')

# 5. Success message
content = content.replace(
    'st.success("Financial Audit completed successfully!")',
    'calculated_income = state.processed_data["ratios"].get("monthly_income", 0.0)\n                    st.success(f"✅ CSV Processed! Accurately Detected Monthly Income: {selected_symbol}{calculated_income:,.2f}")'
)

with open('app.py', 'w') as f:
    f.write(content)

