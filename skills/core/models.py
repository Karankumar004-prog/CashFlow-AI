from datetime import date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RawTransaction(BaseModel):
    date: date
    raw_description: str
    amount: float
    csv_category: Optional[str] = ""
    csv_type: Optional[str] = ""
    running_balance: float = 0.0
    associated_person: Optional[str] = None

class ProcessedTransaction(RawTransaction):
    clean_merchant: str
    transaction_type: str  # Income, Expense, Transfer, Investment, Loan/Debt, Refund
    category: str
    sub_category: str = "Uncategorized"
    intent: str = "Uncategorized"  # Essential, Lifestyle, Investment, Lending, Debt Payment, etc.
    financial_impact: str = "Uncategorized"  # Fixed Expense, Variable Expense, Wealth Building, etc.
    confidence_score: float
    classification_method: str  # rules, regex, memory, ai, default
    classification_reason: str = ""
    prompt_tokens: Optional[int] = 0
    candidates_tokens: Optional[int] = 0

class StateDict(BaseModel):
    raw_data: Dict[str, Any] = Field(default_factory=lambda: {
        "transactions": [],  # List of RawTransaction dicts/objects
        "assets": [],
        "liabilities": [],
        "monthly_income": 0.0,
        "currency_name": "USD",
        "currency_symbol": "$"
    })
    processed_data: Dict[str, Any] = Field(default_factory=lambda: {
        "transactions": [],  # List of ProcessedTransaction dicts/objects
        "ratios": {
            "savings_rate": 0.0,
            "debt_ratio": 0.0,
            "emergency_runway_months": 0.0,
            "asset_coverage": 0.0
        },
        "financial_health_score": 0.0,
        "behavior": {
            "spending_trends": {},
            "category_concentration": [],
            "potential_risk_indicators": [],
            "people_summary": {}
        },
        "telemetry": {
            "execution_time_sec": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost_usd": 0.0
        }
    })
    user_memory: Dict[str, Any] = Field(default_factory=lambda: {
        "overrides": {}  # Description to dict mapping
    })
    agent_outputs: Dict[str, Any] = Field(default_factory=lambda: {
        "quick_wins": [],
        "roadmap": ""
    })
