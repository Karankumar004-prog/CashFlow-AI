# User Stories: CashFlow AI

This document details the user stories, acceptance criteria, and specific scenarios that CashFlow AI will support for its MVP launch.

---

## Personas

1. Fiona the Freelancer: Irregular monthly income, struggles with cash flow planning, business vs. personal expenses, tax tracking.
2. Sam the Salaried Employee: Stable income, subscriptions, wants emergency funds.
3. David the Debt-Struggler: Credit cards, student loans, high interest.

---

## Core User Stories

### US-1: Automated Financial Data Upload & Mapping
**As a** user uploading my bank statements,  
**I want** the system to automatically recognize and parse my CSV/Excel columns (such as Date, Description, and Amount),  
**So that** I do not have to waste time manually reformatting my bank's transaction exports.

#### Acceptance Criteria:
* **AC-1.1**: The system accepts standard CSV/Excel formats from common banks (e.g. Chase, Bank of America) and custom templates.
* **AC-1.2**: The parser automatically maps headers using deterministic keyword mapping (e.g., matching "Transaction Date" or "Post Date" to "Date").
* **AC-1.3**: If column mapping is ambiguous or fails, the user is presented with simple dropdowns in Streamlit to manually map the columns.
* **AC-1.4**: Malformed rows (missing dates or amount values) are ignored or flagged, allowing the rest of the sheet to load successfully.

---

### US-2: Transaction Type & Merchant Extraction
**As a** user looking at a noisy transaction description (e.g. `"POS PUR CHASE DEBIT STARBUCKS #1234 NY"`),  
**I want** the system to extract the clean merchant name (`"Starbucks"`) and classify the transaction type (e.g., `"Expense"` or `"Transfer"`),  
**So that** my downstream financial analysis is based on structured and correct financial data.

#### Acceptance Criteria:
* **AC-2.1**: The system identifies transaction types accurately: `Income`, `Expense`, `Transfer`, `Investment`, `Loan/Debt`, and `Refund`.
* **AC-2.2**: The system parses out clean merchant/counterparty names by stripping noise (numbers, codes, payment channels, cities).
* **AC-2.3**: Internal transfers (e.g., "Transfer to Savings", "Credit Card Payment from checking") are correctly identified as `Transfer` to prevent double-counting of income or expenses.
* **AC-2.4**: Principal payments to liabilities (e.g., "Student Loan Payment") are classified as `Loan/Debt`, while interest costs are categorized as expenses.

---

### US-3: Hierarchical Transaction Resolution (I.U.S. Cost Efficiency)
**As a** system administrator reviewing API expenses,  
**I want** the transaction processing engine to resolve transactions using a cost-efficient hierarchy (Rules $\rightarrow$ Patterns $\rightarrow$ Memory $\rightarrow$ AI Fallback),  
**So that** the system limits expensive LLM calls to truly unknown transactions.

#### Acceptance Criteria:
* **AC-3.1**: The engine first applies exact matches against standard rule dictionaries (e.g., merchant `Netflix` $\rightarrow$ type `Expense`, category `Wants`).
* **AC-3.2**: The engine secondly applies regular expressions (e.g., `PAYROLL` patterns $\rightarrow$ type `Income`).
* **AC-3.3**: The engine thirdly matches descriptions against a stored override mapping representing user memory.
* **AC-3.4**: Gemini 2.5 Flash is invoked only for transactions that fail all previous steps, keeping average LLM calls under 10% of total transactions.

---

### US-4: Expense Category Mapping
**As a** budget-conscious user,  
**I want** my expense transactions automatically categorized into standard budgeting buckets (Needs, Wants, Savings, Debt Payments),  
**So that** I can accurately see my baseline expenses.

#### Acceptance Criteria:
* **AC-4.1**: The system maps expense transactions to `Needs`, `Wants`, `Savings`, or `Debt Payments` based on standard rules and fallback AI classifications.
* **AC-4.2**: The user can review categorized transactions in a table and override any classification.
* **AC-4.3**: User overrides are stored in memory and applied to subsequent uploads.

---

### US-5: Net Worth & Balance Sheet Construction
**As a** wealth-building user,  
**I want** to record my assets (cash, investments) and liabilities (loans, cards) through forms and file uploads,  
**So that** I can see an accurate, real-time calculation of my Net Worth and leverage ratios.

#### Acceptance Criteria:
* **AC-5.1**: The user can input assets and liabilities manually through Streamlit sliders and input fields or via file upload.
* **AC-5.2**: The system calculates the Net Worth ($Assets - Liabilities$) dynamically.
* **AC-5.3**: The system displays a breakdown of liquid vs. illiquid assets and short-term vs. long-term liabilities.
* **AC-5.4**: The system calculates the Debt-to-Income (DTI) ratio based on monthly income and monthly liability payments.

---

### US-6: Automated Behavioral Financial Assessment
**As a** user seeking to change my spending habits,  
**I want** an AI agent to analyze my transactional behavior over time (volatility, recurring subscriptions, weekend spikes),  
**So that** I can identify patterns of financial leakage.

#### Acceptance Criteria:
* **AC-6.1**: The system computes transaction frequency, weekend spending versus weekday spending, and budget volatility.
* **AC-6.2**: The system identifies active recurring charges (subscription sprawl detection) by checking matching monthly transaction descriptions and amounts.
* **AC-6.3**: The Agent generates clear behavioral insights (e.g., "Your discretionary spending increases by 75% on Fridays and Saturdays").

---

### US-7: Actionable Financial Coach Recommendations
**As a** user who wants clear guidance rather than just charts,  
**I want** the agent to synthesize my financial indicators and offer exactly 3 "Quick Wins" and a long-term goal roadmap,  
**So that** I can start improving my financial health immediately.

#### Acceptance Criteria:
* **AC-7.1**: The system feeds the *summarized data structure* (no PII, aggregated categories) to Gemini 2.5 Flash.
* **AC-7.2**: The agent returns exactly three high-priority, actionable "Quick Wins" with specific estimated monthly savings.
* **AC-7.3**: The agent generates a structured goal plan tailored to the user's specific targets (e.g., "Build a 3-month emergency fund").
* **AC-7.4**: Recommendations are formatted in clean, easy-to-read markdown.

---

### US-8: Interactive Financial Dashboard & Report Export
**As a** user planning my finances,  
**I want** to explore my spending trends interactively and export the agent's full review as a file,  
**So that** I can save my financial plan offline.

#### Acceptance Criteria:
* **AC-8.1**: The Streamlit interface displays responsive plots (e.g. spending over time, asset/liability split).
* **AC-8.2**: The dashboard updates instantly when filters (e.g., date ranges, categorization edits) are applied.
* **AC-8.3**: The user can click a "Download Financial Audit" button to export a compiled report (containing calculations, health score, insights, and recommendations) as a Markdown file.
