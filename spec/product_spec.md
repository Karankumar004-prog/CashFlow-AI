# Product Specification: CashFlow AI

CashFlow AI is an AI-powered Financial Intelligence Agent that goes beyond simple expense tracking to deliver deep financial behavior diagnostics, risk assessment, asset-liability valuation, and personalized, actionable improvement strategies.

By analyzing user-uploaded financial records (CSV, Excel, and later PDF statements), CashFlow AI provides users with a comprehensive financial health audit, custom recommendations, and goal-planning support through an interactive Streamlit interface.

---

## 1. Core Value Proposition & Differentiators

* **Not Just an Expense Tracker**: Traditional tools focus on tracking and visualizing past transactions. CashFlow AI is a *forward-looking reasoning agent* that diagnoses financial behavior, uncovers hidden risks, and provides tailored, step-by-step coaching.
* **Transaction Understanding Layer (Primary Quality Driver)**: Rather than assuming transaction records are clean and pre-categorized, the system features a robust understanding layer. It filters noise, extracts merchant names, classifies transaction types, and assigns budget categories using a deterministic-first fallback hierarchy before performing any financial math.
* **Sustainable & Privacy-First (Google AI Agent Principles)**: Avoids sending raw transaction datasets to the Large Language Model (LLM). Instead, it runs deterministic local computation (e.g., aggregations, cash flow formulas via Pandas) and sends only anonymized, structured financial summaries to Gemini, keeping token consumption low, latency short, and user privacy secure.
* **Skill-Based Architecture**: Modeled as a chain of specialized, testable, and replaceable agent skills. Each skill performs a dedicated task, passing structured state to the next stage in the pipeline.

---

## 2. User Stories & Persona Context
*Detailed user stories are located in [user_stories.md](file:///home/mrwhite/Documents/Applicational%20Development/CashFlow-AI/spec/user_stories.md).*

* **The Freelancer/Gig Worker**: Irregular monthly income, struggles with cash flow planning, has multiple business/personal accounts.
* **The Salaried Employee**: Stable income, subscription fatigue, wants to build an emergency fund.
* **The High-Debt Individual**: High credit card balances, needs structured debt paydown, wants to curb spending leakage.

---

## 3. Functional Requirements

### 3.1. Data Ingestion & State Management
- **FR-1.1**: The system must allow users to upload financial files (CSV, XLSX) via a drag-and-drop Streamlit interface.
- **FR-1.2**: The ingestion pipeline must handle diverse bank templates by mapping column headers (e.g., Date, Description, Amount) to a canonical schema.
- **FR-1.3**: The system must maintain a unified memory state representing the user's financial profile.

### 3.2. Transaction Understanding Layer (`expense_categorization` Skill)
- **FR-2.1: Classification of Transaction Types**: The system must parse each raw description and identify the transaction type as one of the following:
  - **Income**: Regular wages, gig payments, interest credit.
  - **Expense**: Discretionary and essential outflows.
  - **Transfer**: Movement of funds between accounts (e.g. paying credit card bill from checking, transferring cash to savings).
  - **Investment**: Outflows into investment accounts (e.g. buying stocks, mutual funds).
  - **Loan/Debt**: Payments towards principal liabilities (e.g. student loans, mortgage principal).
  - **Refund**: Return of funds from a merchant.
- **FR-2.2: Merchant/Counterparty Extraction**: The system must parse noisy description strings (e.g., `"POS PUR CHASE DEBIT STARBUCKS #1234 NY"`) to extract a clean merchant name (e.g., `"Starbucks"`).
- **FR-2.3: Hierarchical Matcher Strategy**: The system must resolve the type, merchant, and category using a strict hierarchy to minimize costs:
  1. *Rule-Based Classification*: Direct exact matching on known description sub-strings and value signs.
  2. *Pattern Matching*: Regular expression mapping on common bank transaction strings.
  3. *Stored User Memory*: Evaluates local user overrides and learned mappings from previous classifications.
  4. *AI Classification (Fallback)*: Sends only unknown/ambiguous descriptions to Gemini 2.5 Flash.
- **FR-2.4: Expense Category Mapping**: For expense transactions, the system must map them into standard budgeting tiers (`Needs`, `Wants`, `Savings`, `Debt Payments`).

### 3.3. Financial Analysis
- **FR-3.1**: The system must calculate basic cash flow metrics:
  - Net monthly cash flow (Income - Outflows).
  - Savings rate percentage.
  - Burn rate (months of runway based on current cash savings and average expenses).
- **FR-3.2**: The system must capture asset records (cash, investments, real estate) and liability records (loans, mortgages) via files or manual forms.
- **FR-3.3**: The system must calculate Net Worth ($Assets - Liabilities$) and leverage ratios (e.g., Debt-to-Income, Liquid Assets to Monthly Expenses).

### 3.4. Financial Health Scoring & Behavioral Diagnosis
- **FR-4.1**: The system must compute a deterministic **Financial Health Score (0-100)** based on a balanced scorecard of:
  - Savings Rate (25%)
  - Debt Ratio (25%)
  - Emergency Runway (25%)
  - Asset Coverage (25%)
- **FR-4.2**: The Behavioral Analysis skill must analyze transaction cadence and spending categories to flag patterns (e.g., lifestyle creep, subscription sprawl, impulsive weekends).

### 3.5. Risk Detection & Financial Coaching
- **FR-5.1**: The system must flag critical risks (e.g., high interest debt leakage, insufficient liquid runway, single-income dependencies, upcoming cash flow squeeze points).
- **FR-5.2**: The Financial Coach skill must take the structured summaries and produce a markdown-formatted advice report containing:
  - Executive summary of financial health.
  - 3 high-priority, actionable "Quick Wins" (e.g., "Cancel $45/mo unused subscriptions", "Refinance 22% APR credit card").
  - A step-by-step roadmap to achieve their designated goals.

### 3.6. Report Generation & Presentation
- **FR-6.1**: The Streamlit frontend must present interactive dashboards (using Altair or Plotly) showing monthly cash flow trends, net worth splits, and category breakdowns.
- **FR-6.2**: The system must allow users to download a comprehensive PDF or Markdown financial audit report containing all calculations, charts, and recommendations.

---

## 4. Non-Functional Requirements

### 4.1. Performance & Latency
- **NFR-1.1**: Local calculations (Pandas ingestion and aggregations) must execute in under 1 second.
- **NFR-1.2**: LLM-based coaching synthesis using Gemini 2.5 Flash must complete in under 5 seconds.
- **NFR-1.3**: The application must utilize session caching to avoid re-running LLM queries on every UI state change in Streamlit.

### 4.2. Privacy & Data Security
- **NFR-2.1**: The application must process data locally in-memory. Uploaded files must never be permanently saved to disk or shared with third-party databases.
- **NFR-2.2**: No Personally Identifiable Information (PII) such as bank account numbers, social security numbers, or names should be sent in prompt payloads to the LLM. Transactions should be sanitized (amounts, categorized buckets, anonymized descriptions only) before LLM analysis.

### 4.3. Cost & Sustainability
- **NFR-3.1**: The system must minimize token count by summarizing raw transaction lists into aggregate metrics (e.g., "Food: $450/month over 15 transactions") instead of feeding raw line items to the LLM.
- **NFR-3.2**: The default LLM must be Gemini 2.5 Flash to ensure highly cost-effective inferences.

### 4.4. Code Cleanliness & Testability
- **NFR-4.1**: Each skill in the `skills/` directory must expose a clean, public Python function interface (e.g. `run_skill(state: Dict) -> Dict`) that can be unit-tested in isolation using mock data.

---

## 5. Success Metrics

For a competitive Kaggle Capstone submission, success will be evaluated across three main axes:

| Metric Category | Metric Name | Target Value | Measurement Method |
| :--- | :--- | :--- | :--- |
| **System Performance** | Latency | < 6.0 seconds total | End-to-end user request timing |
| **System Performance** | Avg. Token Usage | < 3,000 tokens / run | API token usage logs |
| **AI Quality** | Recommendation Relevance | > 90% Actionable | Human evaluation & LLM-as-a-judge scoring against predefined test profiles |
| **AI Quality** | Understanding Accuracy | > 95% Precision | Classified validation dataset of 200 mock transactions (correct type + merchant) |
| **Code Quality** | Test Coverage | > 80% Unit Test Coverage | Pytest coverage reports |

---

## 6. MVP vs. Future Scope

### MVP Scope (Phase 1)
- **Ingestion**: CSV and Excel file uploads.
- **Understanding**: The hierarchical rule $\rightarrow$ pattern $\rightarrow$ memory $\rightarrow$ AI model for parsing transaction details.
- **Processing**: Pandas-based calculation of metrics (runway, savings rate, debt ratios, health score).
- **LLM Agent**: Gemini 2.5 Flash used for behavioral analysis and coach recommendations.
- **Output**: Interactive Streamlit charts, on-screen executive summary, and downloadable markdown reports.

### Future Scope (Phase 2 & Beyond)
- **Multimodal Ingestion**: Native PDF bank statement processing using Gemini 2.5 Pro/Flash to extract transaction tables directly from bank PDFs.
- **Live Integrations**: Plaid API connection for real-time automated data syncs.
- **Database Persistence**: User logins with secure SQLite/PostgreSQL storage to track net worth and spending behavior over multiple months/years.
- **What-If Simulators**: Agent-led interactive scenarios (e.g., "Show me how buying a $40k car impacts my retirement age and emergency runway").
