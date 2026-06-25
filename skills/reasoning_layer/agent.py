import json
import urllib.request
import urllib.error
from typing import List, Dict, Any

def generate_coach_advice(
    financial_health_score: float,
    ratios: dict,
    top_categories: list,
    risk_flags: list,
    api_key: str = None,
    currency_symbol: str = "$",
    income_concentration: list = None,
    net_cash_flow: float = 0.0,
    monthly_income: float = 0.0,
    total_expenses: float = 0.0,
    months_covered: float = 1.0
) -> dict:
    """
    Sends processed financial statistics to Gemini 2.5 Flash to generate personalized
    financial coaching advice (Quick Wins and a Roadmap) formatted as a JSON object.
    Supports a 'mock' API key mode for unit testing.
    """
    income_concentration = income_concentration or []
    
    # 1. Mock API Mode (for testing without a live network connection / key)
    if not api_key or api_key == "mock":
        return {
            "quick_wins": [
                {
                    "title": "Cancel Streaming Sprawl",
                    "description": "Identify and cancel duplicate streaming memberships to boost your savings rate.",
                    "potential_savings": 15
                },
                {
                    "title": "Build emergency reserves",
                    "description": f"Establish a recurring transfer of {currency_symbol}200/mo to secure your liquidity shield.",
                    "potential_savings": 200
                },
                {
                    "title": "Consolidate Credit Card Debt",
                    "description": "Tackle your highest interest rate credit card balance using the Debt Avalanche method.",
                    "potential_savings": 50
                }
            ],
            "roadmap": "### Financial Coach Roadmap\n\n1. **Secure the Shield**: Focus all discretionary surplus into your High Yield Savings Account until your emergency runway covers at least 3 months.\n2. **Tackle Liabilities**: Automate the minimum payments on all debt accounts while directing extra cash to your highest interest liabilities first.\n3. **Build Long-Term Solvency**: Scale your monthly savings rate to 20% to optimize wealth compounding.",
            "promptTokenCount": 0,
            "candidatesTokenCount": 0
        }

    # 2. Real API request via standard urllib
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Pre-calculate fields to safe defaults
    savings_rate = round(ratios.get("savings_rate", 0.0) * 100.0, 2)
    debt_ratio = round(ratios.get("debt_ratio", 0.0) * 100.0, 2)
    runway = round(ratios.get("emergency_runway_months", 0.0), 2)
    asset_coverage = round(ratios.get("asset_coverage", 999.0), 2)
    
    system_instruction = (
        "You are an elite, highly analytical Financial Coach AI. You are parsing explicit, pre-calculated data.\n"
        "STRICT RULES:\n"
        "1. DO NOT HALLUCINATE DEBT. If Debt Ratio is 0%, you must congratulate the user on being debt-free.\n"
        "2. Base your advice STRICTLY on the Net Cash Flow and provided Categories.\n"
        "3. Keep the Roadmap under 150 words and highly specific to the provided metrics.\n"
        "Return exactly a JSON object with two keys: 'quick_wins' (a list of exactly 3 objects with 'title', 'description', 'potential_savings') and 'roadmap' (a short markdown string).\n"
        "IMPORTANT: The 'potential_savings' field MUST be a raw integer representing the monthly dollar amount (e.g., 50), DO NOT use strings, symbols, or decimals."
    )
    
    user_prompt = f"""
    USER PROFILE METRICS:
    - Statement Period: Covers approximately {months_covered:.1f} month(s) of data
    - Total Statement Income: {currency_symbol}{abs(monthly_income):.2f}
    - Total Statement Expenses: {currency_symbol}{abs(total_expenses):.2f}
    - Net Absolute Cash Flow: {currency_symbol}{net_cash_flow:.2f}
    - Financial Health Score: {financial_health_score}/100
    - Savings Rate: {savings_rate}%
    - Debt Ratio (DTI): {debt_ratio}%
    - Emergency Runway: {runway} months
    - Asset Coverage: {asset_coverage}
    - Income Sources: {json.dumps(income_concentration)}
    - Top Spending Concentrations: {json.dumps(top_categories)}
    - Behavioral Risk Flags: {json.dumps(risk_flags)}

    TASK:
    Generate exactly 3 Quick Wins and a long-term goal roadmap.
    Return ONLY a raw JSON block matching the requested schema.
    IMPORTANT: Use the '{currency_symbol}' symbol for all monetary values in your response.
    """
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean markdown JSON formatting if present
                clean_text = content_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                # Parse the inner JSON string returned by Gemini
                result = json.loads(clean_text)
                usage = res_data.get("usageMetadata", {})
                result["promptTokenCount"] = usage.get("promptTokenCount", 0)
                result["candidatesTokenCount"] = usage.get("candidatesTokenCount", 0)
                return result
        except urllib.error.HTTPError as e:
            if e.code in [503, 500, 429] and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            raise RuntimeError(f"Gemini API connection error: HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Gemini API connection error: {e}")
        except (KeyError, IndexError, ValueError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Failed to parse Gemini API response schema: {e}")
            
    return {}
