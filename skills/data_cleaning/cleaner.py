import re

def clean_transaction_description(raw_description: str) -> str:
    """
    Sanitizes raw bank transaction descriptions to isolate the core merchant/payee name.
    Strips transaction processor prefixes, transaction numbers, hashes, states, and utility keywords.
    """
    if not raw_description:
        return ""
        
    # Convert to uppercase for standardization
    desc = raw_description.upper()
    
    # 1. Indian UPI Parsing (Updated via Ultimate System Sync Protocol)
    if desc.startswith("UPI/"):
        parts = desc.split('/')
        if len(parts) >= 4:
            # Determine if part[4] is a name or a handle/domain
            last_part = parts[4].strip() if len(parts) >= 5 else ""
            handle_markers = ['@', 'OKHDFCBANK', 'OKAXIS', 'OKICICI', 'YBL', 'IBL', 'SBI', 'PAYTM', 'HPV', 'OK']
            if len(last_part) <= 3 or any(m in last_part for m in handle_markers):
                name_str = parts[3]
            else:
                name_str = last_part
            
            # Strip leading phone IDs and email handles
            name_str = re.sub(r'^\d+\s+', '', name_str).strip()
            if '@' in name_str:
                name_str = name_str.split('@')[0]
            desc = name_str.strip()
            
    # 2. Bank String Cleanup (Updated via Ultimate System Sync Protocol)
    elif desc.startswith("NEFT"):
        parts = desc.split('/')
        if len(parts) > 1: desc = parts[-1].strip()
    elif desc.startswith("ACH/"):
        parts = desc.split('/')
        if len(parts) >= 2: desc = parts[1].strip()
        
    # 3. Personal Shorthand Cleanup (Remove people's names after colons)
    if ":" in desc:
        parts = desc.split(':')
        # Assuming the first part is the item and the second is the person
        desc = parts[0].strip()

    # 4. Strip common payment processor prefixes
    prefixes = [
        r"^POS PUR\s+",
        r"^DEBIT CARD PURCHASE\s+",
        r"^DEBIT CARD\s+",
        r"^CHECK CARD\s+",
        r"^ACH WITHDRAWAL\s+",
        r"^ONLINE PAYMENT\s+",
        r"^PAYPAL\s+",
        r"^UPI\s+",
        r"^POS\s+",
        r"^DEBIT\s+",
        r"^CREDIT\s+",
        r"^W/D\s+",
        r"^ACH\s+",
        r"^ONLINE\s+",
        r"^ONLINE TRANSFER\s+",
        r"^OVERRIDE\s+"
    ]
    for pattern in prefixes:
        desc = re.sub(pattern, "", desc)
        
    # 5. Strip transaction numbers, hashes, and generic store numbers (e.g. #1249 or 92049)
    desc = re.sub(r"#\s*\d+", "", desc)
    desc = re.sub(r"\b\d{4,}\b", "", desc)
    
    # 6. Clean punctuation and collapse multiple spaces into single space
    # (Must do this before city/state checks so lookbehinds see standard single spacing)
    desc = re.sub(r"[^\w\s\-\.]", " ", desc)
    desc = re.sub(r"\s+", " ", desc)
    
    # 7. Strip trailing city names preceding state codes (e.g. "SEATTLE WA" or "ALISO VIEJO CA")
    # Enforces that there must be at least one preceding word so we don't clear the whole string.
    states = r"(AL|AK|AS|AZ|AR|CA|CO|CT|DE|DC|FM|FL|GA|GU|HI|ID|IL|IN|IA|KS|KY|LA|ME|MH|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|MP|OH|OK|OR|PW|PA|PR|RI|SC|SD|TN|TX|UT|VT|VI|VA|WA|WV|WI|WY)"
    desc = re.sub(r"(?<=\w\s)\b(?:[A-Z\-\.]+\s+){1,2}" + states + r"$", "", desc)
    
    # 8. Strip state code if it is trailing by itself at the end
    desc = re.sub(r"\b" + states + r"$", "", desc)
    
    # 9. Strip generic transaction words that clutter the merchant name
    generic_words = [
        r"\bSTORE\b", r"\bVENDOR\b", r"\bSUB\b", r"\bCHARGE\b", 
        r"\bEPAYMENT\b", r"\bPYMT\b", r"\bAUTOPAY\b", r"\bON-LINE\b", 
        r"\bONLINE\b", r"\bWWW\.\b", r"\b.COM\b", 
        r"\bBILL\b", r"\bPOS\b"
    ]
    for pattern in generic_words:
        desc = re.sub(pattern, "", desc)
        
    # 10. Final clean up of spacing
    desc = re.sub(r"\s+", " ", desc)
    
    return desc.strip()
