# Financial Health Score Methodology: CashFlow AI

To provide real-world utility and maintain testability, CashFlow AI uses a **fully deterministic scorecard** to calculate the user's Financial Health Score (0-100). The Large Language Model (Gemini) does *not* calculate this score; it only interprets the results qualitatively.

The score is composed of four equally-weighted components (25% each):
1. **Savings Rate Component** (25 points)
2. **Debt Ratio Component** (25 points)
3. **Emergency Runway Component** (25 points)
4. **Asset Coverage Component** (25 points)

---

## 1. Component Formulas & Scoring Curves

### 1.1. Savings Rate Score ($Score_{savings}$, Max 25 points)
Measures the proportion of income saved monthly.
* **Formula**:
  $$S = \frac{\text{Monthly Income} - \text{Monthly Expenses}}{\text{Monthly Income}}$$
* **Scoring Rules**:
  - If $S \ge 0.20$ (20% or more saved): **25 points** (Optimal)
  - If $0 \le S < 0.20$:
    $$Score_{savings} = S \times 125 \text{ points}$$
  - If $S < 0$ (Spending exceeds income): **0 points** (Deficit)

### 1.2. Debt Ratio Score ($Score_{debt}$, Max 25 points)
Measures the debt payment burden relative to monthly income (akin to Debt-to-Income / DTI ratio).
* **Formula**:
  $$D = \frac{\text{Monthly Debt Payments}}{\text{Monthly Income}}$$
* **Scoring Rules**:
  - If $D \le 0.15$ (Healthy debt load): **25 points** (Optimal)
  - If $0.15 < D \le 0.50$:
    $$Score_{debt} = 25 - \left(\frac{D - 0.15}{0.35} \times 25\right) \text{ points}$$
  - If $D > 0.50$ (Severe debt burden): **0 points**
  - If the user has **no debt payments** ($D = 0$): **25 points**

### 1.3. Emergency Runway Score ($Score_{runway}$, Max 25 points)
Measures how many months of essential living expenses are covered by liquid cash reserves.
* **Formula**:
  $$R = \frac{\text{Liquid Cash Savings}}{\text{Monthly Essential Expenses}}$$
  *Note: Monthly Essential Expenses are defined as Needs + Debt Payments.*
* **Scoring Rules**:
  - If $R \ge 6 \text{ months}$: **25 points** (Optimal emergency fund)
  - If $0 \le R < 6 \text{ months}$:
    $$Score_{runway} = \frac{R}{6} \times 25 \text{ points}$$

### 1.4. Asset Coverage Score ($Score_{assets}$, Max 25 points)
Measures long-term solvency by comparing total asset value to total outstanding liabilities.
* **Formula**:
  $$A = \frac{\text{Total Assets}}{\text{Total Liabilities}}$$
* **Scoring Rules**:
  - If the user has **no liabilities** (Debt = 0): **25 points**
  - If $A \ge 3.0$ (Assets are triple the liabilities): **25 points**
  - If $1.0 \le A < 3.0$ (Solvent but leveraged):
    $$Score_{assets} = \frac{A - 1.0}{2.0} \times 25 \text{ points}$$
  - If $A < 1.0$ (Insolvent/Negative Net Worth): **0 points**

---

## 2. Combined Score Calculation

The final Financial Health Score is the simple sum of the four component scores:
$$\text{Financial Health Score} = Score_{savings} + Score_{debt} + Score_{runway} + Score_{assets}$$

---

## 3. Score Interpretations

The system maps the numeric score to a classification tier to help prompt the agent's coaching tone:

| Score Range | Category | Financial Status Description | Coaching Tone |
| :--- | :--- | :--- | :--- |
| **85 - 100** | **Excellent** | Strong cash reserves, healthy savings rate, low or zero debt burden, highly solvent. | Encouraging, wealth-optimization and investment focus. |
| **70 - 84** | **Good** | Stable finances, solid cash cushion, manageable debt load. | Growth-focused, building efficiency and automating savings. |
| **50 - 69** | **Fair** | Financially vulnerable. Either emergency reserves are low or spending is high. | Tactical, targeting high discretionary costs and building runway. |
| **0 - 49** | **Needs Attention**| Critical risk. Negative net cash flow, insolvent, or severe debt burden. | Urgent, defensive budgeting, debt consolidation, and basic stability. |
