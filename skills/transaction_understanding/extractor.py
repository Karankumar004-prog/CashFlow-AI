import re
from typing import Optional

# Common generic words that shouldn't be extracted as names
STOP_WORDS = {
    'books', 'book', 'expense', 'rent', 'fee', 'salary', 'grocery', 'food', 
    'medical', 'shopping', 'transfer', 'loan', 'refund', 'payment', 'cash', 
    'atm', 'withdrawal', 'deposit', 'tax', 'bill', 'insurance', 'interest'
}

def extract_associated_person(raw_description: str) -> Optional[str]:
    """
    Attempts to extract a human name from a transaction description using regex heuristics.
    Looks for patterns like "Books: Raj", "Books for Raj", "Books, Raj".
    """
    # Look for patterns indicating a person
    # Pattern 1: for <Name> (e.g. Books for Raj)
    match_for = re.search(r'\bfor\s+([A-Z][a-z]+)\b', raw_description)
    if match_for:
        name = match_for.group(1)
        if name.lower() not in STOP_WORDS:
            return name
            
    # Pattern 2: : <Name> (e.g. Books: Raj)
    match_colon = re.search(r':\s*([A-Z][a-z]+)\b', raw_description)
    if match_colon:
        name = match_colon.group(1)
        if name.lower() not in STOP_WORDS:
            return name
            
    # Pattern 3: , <Name> (e.g. Books, Raj)
    match_comma = re.search(r',\s*([A-Z][a-z]+)\b', raw_description)
    if match_comma:
        name = match_comma.group(1)
        if name.lower() not in STOP_WORDS:
            return name
            
    # Pattern 4: Standalone capitalized word at the start or end, maybe?
    # Actually, let's keep it simple and safe for now to avoid false positives.
    
    # We can also check if a word is capitalized and it is a known name or just not a stop word,
    # but the above patterns cover the user's specific examples.
    # Let's add a check for "to <Name>" or "from <Name>"
    match_to_from = re.search(r'\b(?:to|from)\s+([A-Z][a-z]+)\b', raw_description)
    if match_to_from:
        name = match_to_from.group(1)
        if name.lower() not in STOP_WORDS:
            return name
            
    return None
