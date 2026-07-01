from typing import List
from skills.core.models import ProcessedTransaction
from collections import defaultdict

def detect_recurring_transactions(transactions: List[ProcessedTransaction]) -> List[dict]:
    """Deterministically finds recurring bills by evaluating time deltas and amount variance."""
    groups = defaultdict(list)
    for tx in transactions:
        if tx.transaction_type == "Expense" and tx.clean_merchant:
            groups[tx.clean_merchant].append(tx)

    recurring_items = []

    for merchant, txs in groups.items():
        if len(txs) < 2:
            recurring_items.append({
                "merchant": merchant,
                "amount": abs(txs[0].amount),
                "frequency": "Potential Recurring",
                "occurrences": 1,
                "category": txs[0].category
            })
            continue

        txs.sort(key=lambda x: x.date)

        amounts = [abs(t.amount) for t in txs]
        avg_amt = sum(amounts) / len(amounts)
        max_variance = max(abs(a - avg_amt) / avg_amt for a in amounts) if avg_amt > 0 else 0

        deltas = [(txs[i].date - txs[i-1].date).days for i in range(1, len(txs))]
        avg_delta = sum(deltas) / len(deltas)

        is_recurring = False
        frequency = "Unknown"

        # Allow 20% variance for utility bills
        if max_variance <= 0.20:
            if 25 <= avg_delta <= 35:
                is_recurring, frequency = True, "Monthly"
            elif 6 <= avg_delta <= 8:
                is_recurring, frequency = True, "Weekly"
            elif 350 <= avg_delta <= 380:
                is_recurring, frequency = True, "Annual"

        if is_recurring:
            recurring_items.append({
                "merchant": merchant,
                "amount": avg_amt,
                "frequency": frequency,
                "occurrences": len(txs),
                "category": txs[0].category
            })

    return sorted(recurring_items, key=lambda x: x["amount"], reverse=True)
