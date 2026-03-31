#!/usr/bin/env python3
"""
Boek trade profit als nieuwe transactie
Usage: python3 book_trade_profit.py <amount>
"""
import json
import sys
from datetime import datetime, timezone
from uuid import uuid4

def book_trade_profit(amount_eur: float, description: str = None):
    """Book trade profit as new transaction"""
    
    # Load transactions
    with open('/app/backend/data/financial/transactions.json', 'r') as f:
        data = json.load(f)
    
    # Create trade_profit transaction
    if description is None:
        description = f'Trading winst - €{amount_eur:.2f}'
    
    trade_profit_tx = {
        'id': str(uuid4()),
        'user_id': 'user-000',  # Spark system account
        'type': 'trade_profit',
        'amount_eur': round(amount_eur, 2),
        'token_amount': 0,
        'price_per_token': 0,
        'description': description,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'completed'
    }
    
    # Add to transactions
    data['transactions'].append(trade_profit_tx)
    
    # Save
    with open('/app/backend/data/financial/transactions.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Trade profit geboekt: €{amount_eur:.2f}")
    print(f"   User: user-000 (Spark systeem)")
    print(f"   Description: {description}")
    
    # Show new total
    transactions = data['transactions']
    total_eur = 0
    for tx in transactions:
        if tx['type'] == 'deposit':
            total_eur += tx['amount_eur']
        elif tx['type'] == 'buy_roar':
            total_eur -= tx['amount_eur']
        elif tx['type'] == 'trade_profit':
            total_eur += tx['amount_eur']
    
    roar_tokens = sum(tx['token_amount'] for tx in transactions if tx['type'] == 'buy_roar')
    roar_value = roar_tokens * 5.08
    
    print()
    print(f"💰 Nieuwe staat:")
    print(f"   EUR in systeem: €{total_eur:.2f}")
    print(f"   ROAR tokens: {roar_tokens} (€{roar_value:.2f})")
    print(f"   Totaal vermogen: €{total_eur + roar_value:.2f}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 book_trade_profit.py <amount>")
        print("Example: python3 book_trade_profit.py 50.00")
        sys.exit(1)
    
    amount = float(sys.argv[1])
    description = sys.argv[2] if len(sys.argv) > 2 else None
    
    book_trade_profit(amount, description)
