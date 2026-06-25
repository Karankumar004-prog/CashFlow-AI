from skills.core.models import StateDict

def run_report_generation(state: StateDict) -> str:
    """
    Compiles calculated financial data, behavior indicators, and AI coach recommendations
    into a comprehensive, print-ready Markdown report.
    """
    # 1. Extract state details
    score = state.processed_data.get("financial_health_score", 0.0)
    ratios = state.processed_data.get("ratios", {})
    behavior = state.processed_data.get("behavior", {})
    concentrations = behavior.get("category_concentration", [])
    risks = behavior.get("potential_risk_indicators", [])
    intent_concentrations = behavior.get("intent_concentration", [])
    impact_concentrations = behavior.get("impact_concentration", [])
    people_summary = behavior.get("people_summary", {})
    
    outputs = state.agent_outputs or {}
    quick_wins = outputs.get("quick_wins", [])
    if not isinstance(quick_wins, list):
        quick_wins = []
    roadmap = outputs.get("roadmap", "")
    
    # Pre-format ratios safely
    savings_rate = ratios.get("savings_rate", 0.0) * 100.0
    debt_ratio = ratios.get("debt_ratio", 0.0) * 100.0
    runway = ratios.get("emergency_runway_months", 0.0)
    asset_coverage = ratios.get("asset_coverage", 999.0)
    
    monthly_income_avg = ratios.get("monthly_income", 0.0)
    total_expenses_avg = ratios.get("total_expenses", 0.0)
    total_absolute_income = ratios.get("total_absolute_income", monthly_income_avg)
    total_absolute_expenses = ratios.get("total_absolute_expenses", total_expenses_avg)
    net_absolute_cash_flow = ratios.get("net_absolute_cash_flow", ratios.get("net_cash_flow", 0.0))
    months_covered = ratios.get("months_covered", 1.0)
    currency_symbol = state.raw_data.get("currency_symbol", "$")
    
    coverage_str = f"{asset_coverage:.2f}" if asset_coverage < 999.0 else "999.00 (No Debt)"
    
    # 2. Start formatting Markdown report
    lines = [
        "# CashFlow AI Financial Audit Report",
        "",
        f"## 1. Financial Health Score: {score:.1f}/100",
        "",
        "## 2. Cash Flow Summary",
        "",
        f"- **Total Statement Income:** {currency_symbol}{total_absolute_income:,.2f}",
        f"- **Total Statement Expenses:** {currency_symbol}{total_absolute_expenses:,.2f}",
        f"- **Net Absolute Cash Flow:** {currency_symbol}{net_absolute_cash_flow:,.2f}",
        f"- *Note: Data covers {months_covered:.1f} months. The ratios below are calculated using monthly averages.*",
        "",
        "## 3. Core Metrics",
        "",
        "| Metric | Current Value | Target Threshold | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Savings Rate** | {savings_rate:.1f}% | >= 20.0% | {'✓ Optimal' if savings_rate >= 20.0 else '✗ Suboptimal'} |",
        f"| **Debt Ratio (DTI)** | {debt_ratio:.1f}% | <= 15.0% | {'✓ Optimal' if debt_ratio <= 15.0 else '✗ High Burden'} |",
        f"| **Emergency Runway** | {runway:.1f} months | >= 6.0 months | {'✓ Optimal' if runway >= 6.0 else '✗ Low Reserves'} |",
        f"| **Asset Coverage** | {coverage_str} | >= 3.00 | {'✓ Solvent' if asset_coverage >= 3.0 or asset_coverage >= 999.0 else '✗ Highly Leveraged'} |",
        "",
        "## 4. Behavioral Analysis",
        ""
    ]
    
    # Top Category Concentrations
    lines.append("### Spending Category Concentrations:")
    if isinstance(concentrations, list) and concentrations:
        for item in concentrations:
            if isinstance(item, dict):
                cat = item.get('category', 'Unknown')
                pct = item.get('percentage', 0.0)
                lines.append(f"- **{cat}**: {pct:.1f}% of total outflow")
    else:
        lines.append("- No expense transactions recorded.")
    lines.append("")
    
    # Intent Concentrations
    lines.append("### Spending Intent Concentrations:")
    if isinstance(intent_concentrations, list) and intent_concentrations:
        for item in intent_concentrations:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('intent', 'Unknown')}**: {item.get('percentage', 0.0):.1f}% of total outflow")
    else:
        lines.append("- No intent data recorded.")
    lines.append("")
    
    # Impact Concentrations
    lines.append("### Financial Impact Concentrations:")
    if isinstance(impact_concentrations, list) and impact_concentrations:
        for item in impact_concentrations:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('impact', 'Unknown')}**: {item.get('percentage', 0.0):.1f}% of total outflow")
    else:
        lines.append("- No financial impact data recorded.")
    lines.append("")
    
    # Risk Indicators
    lines.append("### Detected Risk Indicators:")
    if risks:
        for risk in risks:
            lines.append(f"- ⚠️ {risk}")
    else:
        lines.append("- ✓ No major deterministic risk indicators detected.")
    lines.append("")
    
    # People & Relationships
    lines.append("### People & Relationships (Expense Score):")
    if isinstance(people_summary, dict) and people_summary:
        currency_symbol = state.raw_data.get("currency_symbol", "$")
        for person, total in people_summary.items():
            try:
                lines.append(f"- **{person}**: {currency_symbol}{float(total):,.2f} spent on/for them")
            except (ValueError, TypeError):
                lines.append(f"- **{person}**: {currency_symbol}0.00 spent on/for them")
    else:
        lines.append("- No specific people identified in transactions.")
    lines.append("")
    
    # Weekly Spending Breakdown
    lines.append("### Weekly Spending Breakdown")
    lines.append("")
    weekly_spending = behavior.get("weekly_spending", [])
    if isinstance(weekly_spending, list) and weekly_spending:
        currency_symbol = state.raw_data.get("currency_symbol", "$")
        lines.append("| Week Number | Total Spent |")
        lines.append("| :--- | :--- |")
        for item in weekly_spending:
            if isinstance(item, dict):
                lines.append(f"| {item.get('week_number', '?')} | {currency_symbol}{item.get('total_spent', 0.0):.2f} |")
    else:
        lines.append("- No weekly spending data available.")
    lines.append("")
    
    # Category Transparency
    lines.append("### Category Transparency (Merchants mapped per category)")
    lines.append("")
    category_transparency = behavior.get("category_transparency", {})
    if category_transparency:
        for cat, merchants in category_transparency.items():
            merchants_str = ", ".join(merchants) if merchants else "None"
            lines.append(f"- **{cat}**: {merchants_str}")
    else:
        lines.append("- No merchant mapping data available.")
    lines.append("")
    
    # 3. Ingest AI coach outputs
    lines.append("## 5. AI Coach Recommendations")
    lines.append("")
    
    lines.append("### Top 3 Actionable Quick Wins:")
    if isinstance(quick_wins, list) and quick_wins:
        currency_symbol = state.raw_data.get("currency_symbol", "$")
        for idx, win in enumerate(quick_wins, 1):
            if not isinstance(win, dict):
                continue
            title = win.get("title", f"Quick Win {idx}")
            desc = win.get("description", "")
            savings = win.get("potential_savings", 0)
            try:
                savings_val = float(str(savings).replace(currency_symbol, "").replace("$", "").replace(",", ""))
            except ValueError:
                savings_val = 0
                
            savings_str = f"{currency_symbol}{savings_val:,.0f}/mo" if savings_val > 0 else str(savings) if savings else "N/A"
            lines.append(f"{idx}. **{title}** - {desc} *(Potential Monthly Savings: {savings_str})*")
    else:
        lines.append("- No recommendations generated.")
    lines.append("")
    
    lines.append("### Goal Roadmap:")
    if roadmap:
        lines.append(roadmap)
    else:
        lines.append("- No long-term roadmap generated.")
        
    return "\n".join(lines)
