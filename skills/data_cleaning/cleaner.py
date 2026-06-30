import re

def clean_transaction_description(raw_description: str) -> str:
    """
    Sanitizes raw bank transaction descriptions to isolate the core merchant/payee name.
    Strips transaction processor prefixes, transaction numbers, hashes, states, and utility keywords.
    """
    if not raw_description:
        return ""
    
    desc = raw_description.upper()
    
    # 3. Interest, Cash, ATM
    if "INT.PD" in desc:
        return "INTEREST PAID"
    elif desc.startswith("BY CASH") or desc.startswith("CASH DEP"):
        return "CASH DEPOSIT"
    elif desc.startswith("ATM DEP"):
        return "ATM DEPOSIT"
    elif desc.startswith("ATM WDR"):
        return "ATM WITHDRAWAL"
    elif "SMS CHRG" in desc or desc == "CHARGE":
        return "BANK CHARGES"
        
    # 1. Indian UPI Parsing
    if desc.startswith("UPI/") or desc.startswith("UPI-REV/"):
        parts = desc.split('/')
        if len(parts) >= 4:
            # Format A: UPI/ID/P2M/PHONE   VPA/SUFFIX
            # Format B: UPI/ID/P2M/VPA@BANK/NAME
            # Check if parts[3] has space (likely Format A)
            if "   " in parts[3]:
                # Format A
                p3 = parts[3].strip()
                sub_parts = p3.split()
                if len(sub_parts) > 1:
                    desc = sub_parts[-1] # take the vpa
                else:
                    desc = p3
                if '@' in desc:
                    desc = desc.split('@')[0]
            elif len(parts) >= 5:
                # Format B
                vpa = parts[3]
                name = parts[4].strip()
                # If name is highly truncated, fallback to VPA
                if len(name) <= 4 and '@' in vpa:
                    name = vpa.split('@')[0]
                desc = name
                
            # Clean leading digits only if followed by a space (preserves raw phone numbers)
            cleaned_desc = re.sub(r'^\d+\s+', '', desc)
            if cleaned_desc.strip() != "":
                desc = cleaned_desc

    # 2. NEFT / IMPS / RTGS / ACH
    elif desc.startswith("NEFT"):
        if "CMS" in desc:
            parts = desc.split('/')
            if len(parts) >= 3:
                desc = parts[-1].strip()
        else:
            desc = desc.replace("NEFT", "").strip()
            desc = re.sub(r"^NEFT_IN\s*:\s*", "", desc)
            
    elif desc.startswith("IMPS-IN/"):
        parts = desc.split('/')
        if len(parts) >= 4:
            desc = parts[3].strip()
            
    elif desc.startswith("ACH/"):
        parts = desc.split('/')
        if len(parts) >= 2:
            desc = parts[1].strip()
            
    elif desc.startswith("NPCI/ECS"):
        parts = desc.split('/')
        if len(parts) >= 5:
            desc = parts[4].strip()
            
    # 4. Personal Shorthand (e.g. Books: Raj, Books for Raj, Books, Raj)
    if ":" in desc:
        parts = desc.split(':')
        desc = parts[0].strip()
    elif "," in desc:
        parts = desc.split(',')
        desc = parts[0].strip()

    # 5. Strip common prefixes
    prefixes = [
        r"^POS PUR\s+", r"^DEBIT CARD PURCHASE\s+", r"^DEBIT CARD\s+", r"^CHECK CARD\s+",
        r"^ACH WITHDRAWAL\s+", r"^ONLINE PAYMENT\s+", r"^PAYPAL\s+", r"^UPI\s+",
        r"^POS\s+", r"^DEBIT\s+", r"^CREDIT\s+", r"^W/D\s+", r"^ACH\s+",
        r"^ONLINE\s+", r"^ONLINE TRANSFER\s+", r"^OVERRIDE\s+"
    ]
    for pattern in prefixes:
        desc = re.sub(pattern, "", desc)

    # 6. Strip transaction numbers, hashes
    desc = re.sub(r"#\s*\d+", "", desc)
    desc = re.sub(r"\b\d{4,}\b", "", desc)

    # 7. Clean punctuation and spaces (except dot and hyphen)
    desc = re.sub(r"[^\w\s\-\.]", " ", desc)
    
    # Strip trailing city names preceding state codes (e.g. "SEATTLE WA" or "ALISO VIEJO CA")
    # Enforces that there must be at least one preceding word so we don't clear the whole string.
    states = r"(AL|AK|AS|AZ|AR|CA|CO|CT|DE|DC|FM|FL|GA|GU|HI|ID|IL|IN|IA|KS|KY|LA|ME|MH|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|MP|OH|OK|OR|PW|PA|PR|RI|SC|SD|TN|TX|UT|VT|VI|VA|WA|WV|WI|WY)"
    desc = re.sub(r"(?<=\w\s)\b(?:[A-Z\-\.]+\s+){1,2}" + states + r"$", "", desc)
    
    # Strip state code if it is trailing by itself at the end
    desc = re.sub(r"\b" + states + r"$", "", desc)
    
    desc = re.sub(r"\b\.COM\b", "", desc)

    generic_words = [
        r"\bSTORE\b", r"\bVENDOR\b", r"\bSUB\b", r"\bCHARGE\b", 
        r"\bEPAYMENT\b", r"\bPYMT\b", r"\bAUTOPAY\b", r"\bON-LINE\b", 
        r"\bONLINE\b", r"\bWWW\.\b", r"\bBILL\b", r"\bPOS\b"
    ]
    for pattern in generic_words:
        desc = re.sub(pattern, "", desc)
        
    desc = re.sub(r"\s+", " ", desc)
    return desc.strip()
