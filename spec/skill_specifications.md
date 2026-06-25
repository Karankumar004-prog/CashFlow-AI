# Skill Specifications: CashFlow AI

This document defines the functional scope, interface contracts, logic design, and test strategies for the five core skills of CashFlow AI.

---

## 1. Skill: `expense_categorization` (Transaction Ingestion & Understanding)
* **Location**: `skills/expense_categorization/`
* **Purpose**: Parse raw transactions, standardize headers, extract merchant names, identify transaction types, and assign budget categories.

### 1.1. Interface Contract
* **Inputs**:
  - `raw_data.transactions_df` (Pandas DataFrame with arbitrary columns)
* **Outputs**:
  - `processed_data.transactions_df` (Pandas DataFrame with standard columns: `date` [datetime], `raw_description` [str], `clean_merchant` [str], `amount` [float], `transaction_type` [str], `category` [str])

### 1.2. Logic Design
1. **Header Mapping**: Standardizes column names by mapping synonyms (e.g. "Post Date", "Txn Date" $\rightarrow$ "date"; "Description", "Merchant Name" $\rightarrow$ "raw_description"; "Amount", "Value" $\rightarrow$ "amount").
2. **Merchant Extraction**: Strips transaction noise (e.g., IDs, transaction numbers, dates, payment channels, cities, store codes) using regular expression substitutions:
   - Example pattern: `r"(POS PUR|DEBIT|CREDIT|#\d+|STORE|\b[A-Z]{2}\b)"` replaced with empty space, then stripping white space.
3. **Hierarchical Resolution Pipeline**:
   - **Step 1: Rules (Exact Matches)**: Matches the raw or cleaned description against a dictionary of known merchants to assign type and category (e.g., `"Netflix"` $\rightarrow$ Type: `Expense`, Category: `Wants`).
   - **Step 2: Patterns (Regex Matches)**: Evaluates regex patterns for broader classes:
     - `r".*PAYROLL.*|.*DIRECT DEP.*"` $\rightarrow$ Type: `Income`.
     - `r".*TRANSFER.*|.*TRNSFR.*"` $\rightarrow$ Type: `Transfer`.
     - `r".*FIDELITY.*|.*VANGUARD.*"` $\rightarrow$ Type: `Investment`.
     - `r".*PAYMENT.*|.*LOAN.*"` $\rightarrow$ Type: `Loan/Debt`.
   - **Step 3: Stored Override Memory**: Reads user-defined corrections from `user_memory.overrides` and applies them if a description matches.
   - **Step 4: AI Fallback**: Gathers all unique remaining descriptions and invokes Gemini 2.5 Flash using the following strict template layout:
      ```text
      SYSTEM: You are a Financial Data Extractor and Classifier. Your job is to analyze obscure or noisy bank transaction descriptions and map them to strict, predefined categories. 

      You must return a single JSON object with exactly three keys: "transaction_type", "category", and "merchant_name".

      RULES for "transaction_type": 
      You must choose exactly one of the following: ["Income", "Expense", "Transfer", "Investment", "Loan/Debt", "Refund"].

      RULES for "category":
      You must choose exactly one of the following: ["Needs", "Wants", "Savings", "Debt Payments", "Income", "Other"].

      RULES for "merchant_name":
      Extract the clean, readable name of the vendor or counterparty. Strip out all transaction hashes, dates, city names, store numbers, and payment processor prefixes (e.g., "POS PUR", "UPI", "PAYPAL"). If it is an individual's name via a peer-to-peer transfer, capitalize it properly.

      USER INPUT:
      Description: {raw_description}
      Amount: {amount}
      ```
4. **Transaction Type Semantics**:
   - **Income**: Increases cash balances (e.g., salary, refunds).
   - **Expense**: Discretionary/essential outflows.
   - **Transfer**: Inter-account movements (e.g. paying credit card bill from checking).
   - **Investment**: Transfers to investment accounts.
   - **Loan/Debt**: Principal liability paydown.
   - **Refund**: Counter-active expense credit.

### 1.3. Testing Strategy
- **Mock Input**: A DataFrame representing a noisy transaction list:
  - `"POS PUR STARBUCKS #948 NY"` (Amount: -5.50)
  - `"DIRECT DEP PAYROLL"` (Amount: 2500.00)
  - `"TRANSFER TO SAVINGS"` (Amount: -100.00)
- **Assertions**:
  - Row 1: Type `Expense`, Merchant `"Starbucks"`, Category `Wants`.
  - Row 2: Type `Income`, Merchant `"Payroll"`, Category `Income`.
  - Row 3: Type `Transfer`, Merchant `"Savings"`, Category `Savings`.

---

## 2. Skill: `financial_analysis`
* **Location**: `skills/financial_analysis/`
* **Purpose**: Calculate baseline ratios and calculate the Financial Health Score.

### 2.1. Interface Contract
* **Inputs**:
  - `processed_data.transactions_df`
  - `raw_data.monthly_income`
  - `raw_data.assets`
  - `raw_data.liabilities`
* **Outputs**:
  - `processed_data.ratios` (Dict containing the four key ratios)
  - `processed_data.financial_health_score` (Float, 0 to 100)

### 2.2. Logic Design
1. **Ratio Calculations**: Computes the four core ratios:
   - **Savings Rate**: $\frac{\text{Income} - \text{Expenses}}{\text{Income}}$ (Only includes transactions of type `Income` and `Expense`; ignores `Transfers` to avoid double-counting).
   - **Debt Ratio**: $\frac{\text{Monthly Debt Payments}}{\text{Income}}$ (Calculated from transactions of type `Loan/Debt` + manual liability payment records).
   - **Emergency Runway**: $\frac{\text{Liquid Cash Savings}}{\text{Monthly Essential Expenses}}$ (where essential expenses = Needs + Debt Payments).
   - **Asset Coverage**: $\frac{\text{Total Assets}}{\text{Total Liabilities}}$.
2. **Scorecard**: Computes the deterministic **Financial Health Score** as defined in [financial_health_score.md](file:///home/mrwhite/Documents/Applicational%20Development/CashFlow-AI/spec/financial_health_score.md).

### 2.3. Testing Strategy
- **Mock Input**: Standard JSON structures containing predefined incomes, cash savings, assets, liabilities, and transactions.
- **Assertions**:
  - Verify that a user with $0 monthly debt payments gets a 25/25 Debt Ratio component score.
  - Verify that a user with negative cash flow gets 0/25 for the Savings Rate component score.

---

## 3. Skill: `behavior_analysis`
* **Location**: `skills/behavior_analysis/`
* **Purpose**: Perform deterministic pandas analysis to uncover spending trends, category concentrations, and flag risks.

### 3.1. Interface Contract
* **Inputs**:
  - `processed_data.transactions_df`
  - `raw_data.monthly_income`
* **Outputs**:
  - `processed_data.behavior.spending_trends` (Dict containing slope and WoW metrics)
  - `processed_data.behavior.category_concentration` (List of categories sorted by spend)
  - `processed_data.behavior.potential_risk_indicators` (List of warning strings)

### 3.2. Logic Design
1. **Spending Trend Calculation**: Filters transactions of type `Expense` and category `Wants`. Groups transaction values by week, computing the week-over-week change percentage and direction.
2. **Category Concentration**: Aggregates spend per merchant/category and divides by total monthly spend to find the percentage concentration.
3. **Deterministic Risks**:
   - *Cash Flow Deficit*: Set if total outflows > monthly income.
   - *Subscription Sprawl*: Groups transactions matching monthly intervals with identical amounts and merchants to count active recurring charges. Alert if count > 5.
   - *Low Liquidity Shield*: Alert if Cash Savings < 1 month of essential expenses.

### 3.3. Testing Strategy
- **Mock Input**: A dataframe representing 4 weeks of transactions. Week 1 discretionary spend is $100, Week 2 is $200.
- **Assertions**:
  - Trend shows a positive slope (increasing spend).
  - Category concentration calculates the highest category correctly.

---

## 4. Skill: `financial_coach`
* **Location**: `skills/financial_coach/`
* **Purpose**: Prompt a single Gemini 2.5 Flash reasoning agent with calculated statistics to output the top 3 actionable "Quick Wins" and a goal roadmap.

### 4.1. Interface Contract
* **Inputs**:
  - `processed_data.ratios`
  - `processed_data.financial_health_score`
  - `processed_data.behavior`
* **Outputs**:
  - `agent_outputs.quick_wins` (List of 3 dicts: `{"title": str, "description": str, "potential_savings": float}`)
  - `agent_outputs.roadmap` (Markdown string containing the custom plan)

### 4.2. Logic & Prompt Design
We design a strict, low-token prompt that enforces structured JSON response schemas for the quick wins:

```text
SYSTEM: You are a Financial Intelligence Coach. You analyze processed financial scores and behavioral metrics to provide actionable advice. 

CONSTRAINTS:
1. You never do math yourself; you rely entirely on the provided metrics.
2. Do not provide specific investment suggestions (e.g., specific stocks, crypto, or tickers). Focus on cash flow management, debt reduction, and budget efficiency.
3. Keep the tone empathetic but direct.

USER PROFILE METRICS:
- Financial Health Score: {financial_health_score}/100
- Savings Rate: {savings_rate}%
- Debt Ratio (DTI): {debt_ratio}%
- Emergency Runway: {runway} months
- Asset Coverage: {asset_coverage}
- Top Spending Concentrations: {top_categories}
- Behavioral Risk Flags: {risk_flags}

TASK:
Return a JSON object with two keys: "quick_wins" and "roadmap".

1. "quick_wins": A JSON list of exactly 3 actionable steps to immediately improve these metrics. Each step must have a "title" (string), "description" (string), and "potential_savings" (integer representing estimated monthly $ saved, or 0 if not applicable).
2. "roadmap": A markdown-formatted string (under 250 words) outlining a step-by-step long-term plan tailored to the user's specific risks and ratios.
```

### 4.3. Testing Strategy
- **Mock Input**: Standard JSON representation of a poor financial state (DTI 45%, Runway 0.5 months).
- **Assertions**:
  - Response contains exactly 3 quick wins.
  - The recommendations focus on debt reduction or runway building, not investment advice.

---

## 5. Skill: `report_generation`
* **Location**: `skills/report_generation/`
* **Purpose**: Compile all calculated indicators, trends, risk flags, and AI-generated coach roadmaps into a beautiful, portable Markdown format.

### 5.1. Interface Contract
* **Inputs**:
  - Entire unified state (`StateDict`)
* **Outputs**:
  - A compiled, print-ready Markdown document string.

### 5.2. Logic Design
- Combines sections using clean markdown string templates:
  - Header: CashFlow AI Audit Report
  - Score Card: Displays the Financial Health Score as a colored status bar.
  - Ratios: Displays Savings Rate, DTI, Runway, and Solvency in a clean markdown table.
  - Behavior Audit: Prints the top discretionary spending items and detected risk warnings.
  - AI Recommendations: Injects the generated quick wins and roadmap.
- Outputs the complete string to the Streamlit download handler.

### 5.3. Testing Strategy
- **Mock Input**: A populated `StateDict`.
- **Assertions**:
  - Returns a string starting with `# CashFlow AI Audit Report`.
  - Injects all four key metrics and the AI roadmap text.
