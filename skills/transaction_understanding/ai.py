import json
import urllib.request
import urllib.error
from typing import List

def batch_classify_transactions(transactions: List[dict], api_key: str) -> dict:
    """
    Sends a batch of unknown transactions to Gemini 2.5 Flash for categorization.
    Expects transactions to be a list of dicts: [{'description': '...', 'amount': 123.45}]
    Returns a dictionary mapping raw descriptions to their AI-classified properties.
    """
    if not api_key or api_key == "mock":
        return {}
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "You are a transaction classifier. I will provide a JSON list of transactions with 'description', 'amount', and sometimes 'csv_type' and 'csv_category'. "
        "Return a JSON dictionary where the keys are the exact raw descriptions, and the values are objects "
        "containing {'transaction_type': '...', 'category': '...', 'sub_category': '...', 'clean_merchant': '...', 'associated_person': '...'}.\n\n"
        "USE THE CSV METADATA: If the bank provided a 'csv_category' or 'csv_type', use it as a strong hint for your classification.\n\n"
        "CRITICAL RULE: MONEY DIRECTION COMES FIRST:\n"
        "- If amount > 0 (Positive Cash Flow), 'transaction_type' MUST be exactly one of: ['Income', 'Refund', 'Transfer', 'Loan/Debt']\n"
        "- If amount < 0 (Negative Cash Flow), 'transaction_type' MUST be exactly one of: ['Expense', 'Investment', 'Transfer', 'Loan/Debt']\n\n"
        "RULES for 'category':\n"
        "You must choose exactly one of: ['Food', 'Shopping', 'Medical', 'Housing', 'Transport', 'Entertainment', 'Investment', 'Income', 'Transfer', 'Loan/Debt', 'Other'].\n"
        "These functional categories will be mapped to financial intents (e.g., Essential, Lifestyle, Investment) and impacts downstream.\n\n"
        "RULES for 'sub_category':\n"
        "Provide a granular sub-category. Examples: 'Groceries', 'Restaurant', 'Medicine', 'Personal Care', 'Rent', 'Flights', 'Streaming', 'SIP', 'Salary', 'Miscellaneous'.\n"
        "Note: Grooming, salon, or self-care should be categorized as 'Shopping' or 'Medical' with sub_category 'Personal Care'.\n\n"
        "RULES for 'clean_merchant':\n"
        "Extract the clean, readable name of the vendor or counterparty. Strip out all transaction hashes, "
        "dates, city names, store numbers, and payment processor prefixes (e.g., 'POS PUR', 'UPI', 'PAYPAL').\n\n"
        "PARSE PERSONAL SHORTHAND & RELATIONSHIPS: If a description contains names or implies a peer-to-peer split (e.g., 'Books: Raj', 'Chocolate Bowl: Aditya', 'Dinner with Brother'), you MUST analyze the relationship.\n"
        "- Set 'associated_person' to the Name (e.g., 'Raj', 'Aditya', 'Brother').\n"
        "- Set 'clean_merchant' to the underlying Item or context (e.g., 'Books', 'Chocolate Bowl', 'Dinner').\n"
        "- For these relationship-based splits/shares, set Category='Transfer' and Sub-Category='Relational Expense'. If it's a pure loan, use Category='Loan/Debt', Sub-Category='Lending'.\n\n"
        "REPAYMENT LOGIC:\n"
        "If description includes 'Repay', 'Settlement', or 'Refund':\n"
        "- If Amount > 0: Type = Income, Category = Transfer (or Loan/Debt).\n"
        "- If Amount < 0: Type = Loan/Debt, Category = Loan/Debt (with sub_category 'Loan Repayment').\n\n"
        "RULES for 'associated_person':\n"
        "If the description contains a human name indicating who the transaction was for or with, extract that name. Otherwise, set it to null.\n\n"
        "NO NULLS: If merchant is unclear, use the original description string."
    )
    
    user_prompt = json.dumps(transactions)
    
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
    
    import time
    
    max_retries = 4
    for attempt in range(max_retries):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
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
                
                result_dict = json.loads(clean_text)
                
                # Pass token usage along in a special key if we want telemetry, 
                # but for now just return the dictionary
                return result_dict
        except urllib.error.HTTPError as e:
            if e.code in [503, 500, 429, 504] and attempt < max_retries - 1:
                time.sleep((2 ** attempt) + 1)  # Exponential backoff: 2s, 3s, 5s, 9s
                continue
            raise RuntimeError(f"API Call failed: HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) + 1)
                continue
            raise RuntimeError(f"API Call failed: {e}")
            
    return {}
