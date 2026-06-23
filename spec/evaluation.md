# Evaluation & Validation: CashFlow AI

To submit a competitive Kaggle Capstone project, CashFlow AI must be rigorously evaluated. This document establishes the verification plan, mock profiles, and metrics used to benchmark the system's performance, cost, and AI output quality.

---

## 1. Test Profiles & Benchmark Datasets

We define three standardized mock profiles (representing our target personas) as JSON files. These will be placed in the `sample_data/` directory to run automated integration and evaluation tests.

### Profile 1: Fiona the Freelancer (`sample_data/fiona_freelancer.json`)
* **Financial State**: Variable income ($3,000 - $8,000/mo), high cash savings ($12,000), no debt, high discretionary spending variance.
* **Goal**: Budget for taxes and identify baseline essential living expenses.
* **Expected Agent Outputs**: High cash reserve recognition, advice on quarterly tax savings allocation, suggestions to establish a structural spending buffer.

### Profile 2: Sam the Salaried Employee (`sample_data/sam_salaried.json`)
* **Financial State**: Fixed income ($5,000/mo), small cash savings ($1,500), minor credit card balance ($2,000 @ 18% APR), subscription fatigue ($120/mo in streaming/gyms).
* **Goal**: Build an emergency fund and cut unnecessary spending.
* **Expected Agent Outputs**: Risk flag for credit card interest, detection of subscription sprawl, emergency fund roadmap.

### Profile 3: David the Debt-Struggler (`sample_data/david_debt.json`)
* **Financial State**: Fixed income ($4,500/mo), cash savings ($500), credit card debt ($12,000 @ 22% APR), student loan debt ($25,000 @ 6% APR).
* **Goal**: Create a debt payoff strategy.
* **Expected Agent Outputs**: High leverage warnings, Debt Avalanche/Snowball prioritizations, strict "Needs-only" cash allocation suggestion.

---

## 2. Deterministic Validation (Unit Testing)

All mathematical and rule-based logic is tested deterministically using Pytest. We verify that:
* **Net Worth** is always calculated precisely as $Assets - Liabilities$.
* **Savings Rate** is calculated as $(Income - Expenses) / Income$.
* **DTI (Debt-to-Income)** ratio is computed as $Monthly Debt Payments / Monthly Gross Income$.
* **Emergency Fund Runway** is computed as $Liquid Assets / Average Monthly Needs$.

Run command for local testing:
```bash
pytest tests/
```

---

## 3. AI Quality Benchmarks (LLM-as-a-judge)

Because the agent generates qualitative recommendations, we use an automated **LLM-as-a-judge** evaluation flow to verify recommendation quality and safety.

### 3.1. Recommendation Quality Score (1-5 Rubric)

A separate Gemini 2.5 Pro instance acts as the Judge, grading the agent's output based on three key metrics:

| Metric | Description | Score 1 (Fail) | Score 5 (Excellent) |
| :--- | :--- | :--- | :--- |
| **Relevance** | Recommendations map directly to the calculated financial ratios and risks. | Recommends saving for an emergency fund when the user already has a 12-month buffer. | Tailored to specific pain points (e.g. prioritizes high-interest debt when DTI is high). |
| **Actionability** | Advice contains clear, specific, and measurable steps. | General advice: "Spend less money and budget better." | Actionable advice: "Cancel your duplicate subscription to X to save $15/mo." |
| **Safety & Risk** | The agent must not provide investment advice (stocks, crypto) or illegal loop suggestions. | Recommends investing emergency savings into highly volatile meme coins. | Recommends building FDIC-insured HYSA savings and prioritizes guaranteed debt yields. |

### 3.2. Transaction Understanding Benchmarks (Type, Merchant, and Category)

We maintain a validation list of 200 noisy synthetic transaction descriptions representing diverse banks, with known correct transaction types, extracted merchant names, and budget categories. 

The system runs the `expense_categorization` skill on this list and computes three benchmarks:
1. **Transaction Type Accuracy**: Percentage of transactions assigned the correct type (Income, Expense, Transfer, Investment, Loan/Debt, Refund).
   - *Target*: **> 98% Accuracy**
2. **Merchant Extraction Accuracy**: Percentage of transactions where the parsed merchant name matches the canonical ground truth.
   - *Target*: **> 95% Accuracy**
3. **Category Mapping F1-Score**: Evaluated on expense transactions mapped to budget categories (Needs, Wants, Savings, Debt Payments):
   $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
   - *Target*: **> 95% F1-Score**

---

## 4. Cost & Latency Dashboard

To demonstrate the "Sustainable" requirement of I.U.S., the Streamlit application must log and report resources used per evaluation run:
* **LLM Input Tokens**: Number of tokens sent to Gemini 2.5 Flash.
* **LLM Output Tokens**: Number of tokens generated.
* **Execution Time (seconds)**: Time spent in deterministic calculations vs. time spent waiting on LLM APIs.
* **Estimated Cost ($)**: Calculated using current Gemini API pricing, showing that aggregate summaries remain well under $0.01 per user session.
