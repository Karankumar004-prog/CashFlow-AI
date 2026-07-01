import json
import urllib.request
import urllib.error
from typing import List

def batch_classify_transactions(transactions: List[dict], api_key: str) -> dict:
    """
    Sends a batch of unknown transactions to Gemini 2.5 Flash for categorization.
    Expects transactions to be a list of dicts: [{'signature': '...', 'description': '...', 'amount': 123.45}]
    Returns a dictionary mapping raw descriptions (signatures) to their AI-classified properties.
    """
    if not api_key or api_key == "mock":
        return {}
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "You are a transaction classifier. I will provide a JSON list of transactions with 'signature', 'description', 'amount', and sometimes 'csv_type' and 'csv_category'. "
        "Return a JSON ARRAY of objects. Each object MUST contain the 'signature' provided in the input, "
        "along with its classification fields: 'transaction_type', 'category', 'sub_category', 'clean_merchant', and 'associated_person'.\n\n"
        "USE THE CSV METADATA: If the bank provided a 'csv_category' or 'csv_type', use it as a strong hint for your classification.\n\n"
        "CRITICAL RULE: MONEY DIRECTION COMES FIRST:\n"
        "- If amount > 0 (Positive Cash Flow), 'transaction_type' MUST be exactly one of: ['Income', 'Refund', 'Transfer', 'Loan/Debt']\n"
        "- If amount < 0 (Negative Cash Flow), 'transaction_type' MUST be exactly one of: ['Expense', 'Investment', 'Transfer', 'Loan/Debt']\n\n"
        "RULES for 'category':\n"
        "You must choose exactly one of: ['Food', 'Shopping', 'Medical', 'Housing', 'Transport', 'Entertainment', 'Investment', 'Income', 'Transfer', 'Loan/Debt', 'Other'].\n"
        "CRITICAL: NEVER output 'Uncategorized'. If a transaction is vague, ambiguous, or lacks context (e.g., a random person's name or a generic store), you MUST categorize it as 'Other'.\n"
        "If the description contains terms related to health, illness, coughing, doctors, or medicine, you MUST categorize it as 'Medical'.\n\n"
        "RULES for 'sub_category':\n"
        "Provide a granular sub-category. Examples: 'Groceries', 'Restaurant', 'Medicine', 'Personal Care', 'Rent', 'Miscellaneous'.\n"
        "CRITICAL: NEVER output 'Uncategorized'. If you do not know the sub-category, output 'Miscellaneous'.\n\n"
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
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "description": "List of transaction classifications.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "signature": {"type": "STRING"},
                        "transaction_type": {"type": "STRING"},
                        "category": {"type": "STRING"},
                        "sub_category": {"type": "STRING"},
                        "clean_merchant": {"type": "STRING"},
                        "associated_person": {"type": "STRING", "nullable": True}
                    },
                    "required": ["signature", "transaction_type", "category", "sub_category", "clean_merchant"]
                }
            }
        }
    }
    
    import time
    
    max_retries = 5
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
                
                try:
                    # Parse the array returned by Gemini
                    result_list = json.loads(clean_text)
                    
                    # Convert the array of objects back into a dictionary mapping the signature to the data
                    result_dict = {item["signature"]: item for item in result_list if "signature" in item}
                    
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error. Raw output: {clean_text}")
                    raise RuntimeError(f"AI returned invalid JSON: {e}")
                
                usage = res_data.get("usageMetadata", {})
                usage_dict = {
                    "promptTokenCount": usage.get("promptTokenCount", 0),
                    "candidatesTokenCount": usage.get("candidatesTokenCount", 0)
                }
                
                return result_dict, usage_dict
                
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                # If Too Many Requests, wait significantly longer (e.g., 15s, 30s, 60s)
                sleep_time = 15 * (attempt + 1)
                time.sleep(sleep_time)
                continue
            elif e.code in [503, 500, 504] and attempt < max_retries - 1:
                # Standard backoff for server errors
                time.sleep((2 ** attempt) + 1)
                continue
            raise RuntimeError(f"API Call failed: HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) + 1)
                continue
            raise RuntimeError(f"API Call failed: {e}")
            
    return {}, {}
