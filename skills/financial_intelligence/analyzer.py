from typing import List, Dict
from collections import Counter
from skills.core.models import ProcessedTransaction

def calculate_category_concentration(transactions: List[ProcessedTransaction]) -> List[dict]:
    """
    Filters for expense transactions, sums amounts by category,
    and returns category percentages sorted in descending order.
    """
    # 1. Filter expense transactions
    expenses = [tx for tx in transactions if tx.transaction_type.lower() == "expense"]
    
    if not expenses:
        return []
        
    total_expenses = sum(abs(tx.amount) for tx in expenses)
    if total_expenses == 0:
        return []
        
    # 2. Aggregate spend by sub_category
    category_totals = {}
    for tx in expenses:
        cat = tx.sub_category
        category_totals[cat] = category_totals.get(cat, 0.0) + abs(tx.amount)
        
    # 3. Calculate percentages
    concentration = []
    for cat, total in category_totals.items():
        percentage = round((total / total_expenses) * 100.0, 2)
        concentration.append({
            "category": cat,
            "percentage": percentage
        })
        
    # 4. Sort descending by percentage
    concentration.sort(key=lambda x: x["percentage"], reverse=True)
    return concentration

def calculate_income_concentration(transactions: List[ProcessedTransaction]) -> List[dict]:
    """
    Filters for income transactions, sums amounts by clean_merchant (source),
    and returns source percentages sorted in descending order.
    """
    income_txs = [tx for tx in transactions if tx.transaction_type.lower() == "income"]
    
    if not income_txs:
        return []
        
    total_income = sum(abs(tx.amount) for tx in income_txs)
    if total_income == 0:
        return []
        
    source_totals = {}
    for tx in income_txs:
        source = tx.clean_merchant.strip().upper() if tx.clean_merchant else "UNKNOWN"
        source_totals[source] = source_totals.get(source, 0.0) + abs(tx.amount)
        
    concentration = []
    for source, total in source_totals.items():
        percentage = round((total / total_income) * 100.0, 2)
        concentration.append({
            "source": source,
            "percentage": percentage
        })
        
    concentration.sort(key=lambda x: x["percentage"], reverse=True)
    concentration.sort(key=lambda x: x["percentage"], reverse=True)
    return concentration

def calculate_intent_concentration(transactions: List[ProcessedTransaction]) -> List[dict]:
    expenses = [tx for tx in transactions if tx.transaction_type.lower() == "expense"]
    if not expenses:
        return []
        
    total_expenses = sum(abs(tx.amount) for tx in expenses)
    if total_expenses == 0:
        return []
        
    intent_totals = {}
    for tx in expenses:
        intent = getattr(tx, "intent", "Uncategorized")
        intent_totals[intent] = intent_totals.get(intent, 0.0) + abs(tx.amount)
        
    concentration = []
    for intent, total in intent_totals.items():
        percentage = round((total / total_expenses) * 100.0, 2)
        concentration.append({
            "intent": intent,
            "percentage": percentage
        })
        
    concentration.sort(key=lambda x: x["percentage"], reverse=True)
    return concentration

def calculate_impact_concentration(transactions: List[ProcessedTransaction]) -> List[dict]:
    expenses = [tx for tx in transactions if tx.transaction_type.lower() == "expense"]
    if not expenses:
        return []
        
    total_expenses = sum(abs(tx.amount) for tx in expenses)
    if total_expenses == 0:
        return []
        
    impact_totals = {}
    for tx in expenses:
        impact = getattr(tx, "financial_impact", "Uncategorized")
        impact_totals[impact] = impact_totals.get(impact, 0.0) + abs(tx.amount)
        
    concentration = []
    for impact, total in impact_totals.items():
        percentage = round((total / total_expenses) * 100.0, 2)
        concentration.append({
            "impact": impact,
            "percentage": percentage
        })
        
    concentration.sort(key=lambda x: x["percentage"], reverse=True)
    return concentration

def detect_risks(transactions: List[ProcessedTransaction], ratios: dict) -> List[str]:
    """
    Evaluates financial indicators and transaction history to detect behavioral risks.
    """
    risks = []
    
    # 1. Cash Flow Deficit Flag
    # Savings rate < 0 means monthly expenses exceed income
    if ratios.get("savings_rate", 0.0) < 0.0:
        risks.append("Cash Flow Deficit: Outflows exceed income.")
        
    # 2. Low Liquidity Shield Flag
    # Emergency runway < 1.0 month of essential expenses
    if ratios.get("emergency_runway_months", 0.0) < 1.0:
        risks.append("Low Liquidity Shield: Less than 1 month of essential expenses saved.")
        
    # 3. Subscription Sprawl Flag
    # Group expense transactions by (merchant, amount) and count occurrences
    expense_txs = [tx for tx in transactions if tx.transaction_type.lower() == "expense"]
    
    charge_tuples = []
    for tx in expense_txs:
        # Standardize merchant name casing for safer grouping
        merchant = tx.clean_merchant.upper() if tx.clean_merchant else ""
        charge_tuples.append((merchant, abs(tx.amount)))
        
    counts = Counter(charge_tuples)
    
    # Count unique charges that appear more than once
    recurring_charges_count = sum(1 for charge, count in counts.items() if count > 1)
    
    if recurring_charges_count > 5:
        risks.append("Subscription Sprawl: High number of recurring identical charges detected.")
        
    return risks

def calculate_weekly_spending(transactions: List[ProcessedTransaction]) -> List[dict]:
    """
    Filters for expense transactions, groups them by ISO week number,
    and returns a list of dictionaries with week_number and total_spent.
    """
    expenses = [tx for tx in transactions if tx.transaction_type.lower() == "expense"]
    if not expenses:
        return []
        
    weekly_totals = {}
    for tx in expenses:
        week_num = tx.date.isocalendar()[1]
        weekly_totals[week_num] = weekly_totals.get(week_num, 0.0) + abs(tx.amount)
        
    weekly_spending = []
    for week_num, total in weekly_totals.items():
        weekly_spending.append({
            "week_number": week_num,
            "total_spent": round(total, 2)
        })
        
    weekly_spending.sort(key=lambda x: x["week_number"])
    return weekly_spending

def get_category_transparency(transactions: List[ProcessedTransaction]) -> dict:
    """
    Groups unique merchants by category/sub_category.
    """
    transparency = {}
    for tx in transactions:
        cat = f"{tx.category} > {tx.sub_category}"
        merchant = tx.clean_merchant.strip() if tx.clean_merchant else "Unknown"
        if cat not in transparency:
            transparency[cat] = set()
        transparency[cat].add(merchant)
        
    return {cat: sorted(list(merchants)) for cat, merchants in transparency.items()}

def calculate_people_summary(transactions: List[ProcessedTransaction]) -> dict:
    """
    Groups transactions by associated_person and sums up the total amount spent on/by them.
    Returns a dictionary mapping person_name to total_expense_score (absolute sum of expenses).
    """
    people_totals = {}
    for tx in transactions:
        if getattr(tx, "associated_person", None):
            person = tx.associated_person.strip().title()
            if tx.transaction_type.lower() == "expense":
                people_totals[person] = people_totals.get(person, 0.0) + abs(tx.amount)
            # You could also track income from them, but the user specifically asked for "expense score"
                
    # Return sorted by expense descending
    return dict(sorted(people_totals.items(), key=lambda item: item[1], reverse=True))
