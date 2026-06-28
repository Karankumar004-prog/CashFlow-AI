import re
from typing import Optional

# Common generic words that shouldn't be extracted as names
STOP_WORDS = {
    'books', 'book', 'expense', 'rent', 'fee', 'salary', 'grocery', 'food', 
    'medical', 'shopping', 'transfer', 'loan', 'refund', 'payment', 'cash', 
    'atm', 'withdrawal', 'deposit', 'tax', 'bill', 'insurance', 'interest',
    'self', 'home', 'house', 'office', 'personal'
}

def extract_associated_person(raw_description: str) -> Optional[str]:
    """
    Attempts to extract a human name from a transaction description using regex heuristics.
    Looks for patterns like "Books: Raj", "Books for Raj", "Books, Raj".
    """
    if not raw_description:
        return None
        
    desc_clean = re.sub(r'\s+', ' ', raw_description.strip())
    
    # 1. Pattern: for/to/from <Name>
    match_for = re.search(r'\b(?:for|to|from)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', desc_clean, re.IGNORECASE)
    if match_for:
        name = match_for.group(1).strip()
        if name.lower().split()[0] not in STOP_WORDS:
            return name.title()

    # 2. Pattern: : <Name>
    match_colon = re.search(r':\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', desc_clean)
    if match_colon:
        name = match_colon.group(1).strip()
        if name.lower().split()[0] not in STOP_WORDS:
            return name.title()
            
    # 3. Pattern: , <Name>
    match_comma = re.search(r',\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', desc_clean)
    if match_comma:
        name = match_comma.group(1).strip()
        if name.lower().split()[0] not in STOP_WORDS:
            return name.title()
            
    return None

