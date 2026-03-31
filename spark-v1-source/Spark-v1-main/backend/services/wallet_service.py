"""
Wallet Service - Multi-entity wallet system
Manages entities (Spark Core, Spark Your Life, Roadkill Merch, Personal)
and user wallets (tokens, credits, balances)
"""
import os
import json
import time
import uuid
from typing import Dict, Optional, List
from utils.data_manager import DataManager
from services.bitvavo_service import BitvavoService


class WalletService:
    """
    Centralized wallet management voor Spark ecosystem
    """
    
    ENTITIES_PATH = "wallet/entities.json"
    USER_WALLETS_PATH = "wallet/user_wallets.json"
    TRANSACTIONS_PATH = "wallet/transactions.json"
    
    @staticmethod
    def get_entities() -> Dict:
        """
        Haal alle entities op (Spark Core, Spark Your Life, etc)
        
        Returns:
            {"entities": {...}}
        """
        try:
            data = DataManager.load_data(WalletService.ENTITIES_PATH)
            return data.get("entities", {})
        except Exception as e:
            print(f"[WALLET] Error loading entities: {e}")
            return {}
    
    @staticmethod
    def get_entity(entity_id: str) -> Optional[Dict]:
        """
        Haal 1 specifieke entity op
        """
        entities = WalletService.get_entities()
        return entities.get(entity_id)
    
    @staticmethod
    def get_user_wallet(user_id: str) -> Optional[Dict]:
        """
        Haal user wallet op (tokens, credits, etc)
        """
        try:
            data = DataManager.load_data(WalletService.USER_WALLETS_PATH)
            user_wallets = data.get("user_wallets", {})
            return user_wallets.get(user_id)
        except Exception as e:
            print(f"[WALLET] Error loading user wallet: {e}")
            return None
    
    @staticmethod
    def get_entity_balance(entity_id: str, user_id: str = None) -> Dict:
        """
        Bereken totale balans van een entity
        
        Voor Spark Core crypto: haal live data van Bitvavo
        Voor rest: sum manual transactions (1x per entity)
        """
        entity = WalletService.get_entity(entity_id)
        
        if not entity:
            return {"success": False, "error": "Entity not found"}
        
        total_eur = 0.0
        wallets_detail = []
        
        # Check if entity has Bitvavo crypto
        has_bitvavo = False
        for wallet_type, wallet_data in entity.get("wallets", {}).items():
            if wallet_data.get("provider") == "bitvavo" and wallet_data.get("enabled"):
                has_bitvavo = True
                bitvavo_user_id = wallet_data.get("user_id", user_id)
                if bitvavo_user_id:
                    balance_result = BitvavoService.get_balance(bitvavo_user_id)
                    if balance_result.get("success"):
                        crypto_balance = balance_result.get("total_eur", 0.0)
                        total_eur += crypto_balance
                        wallets_detail.append({
                            "type": wallet_type,
                            "balance_eur": crypto_balance,
                            "provider": "bitvavo",
                            "status": "connected"
                        })
                    else:
                        # Bitvavo error - return error state, don't fallback to €0
                        error_msg = balance_result.get("error", "Onbekende fout")
                        
                        # Check for 403 IP restriction
                        if "403" in error_msg or "IP" in error_msg:
                            error_msg = "IP adres niet toegestaan in Bitvavo whitelist"
                        
                        return {
                            "success": False,
                            "error": f"Bitvavo API niet bereikbaar: {error_msg}",
                            "error_type": "bitvavo_connection",
                            "entity_id": entity_id,
                            "entity_name": entity.get("name")
                        }
        
        # For non-bitvavo entities: sum transactions (1x, not per wallet)
        if not has_bitvavo:
            transactions = WalletService.get_transactions(entity_id)
            for tx in transactions.get("transactions", []):
                if tx.get("type") in ["donation", "income"]:
                    total_eur += tx.get("amount", 0)
                elif tx.get("type") == "expense":
                    total_eur -= tx.get("amount", 0)
            
            # Add wallets detail (but balance is already calculated)
            for wallet_type, wallet_data in entity.get("wallets", {}).items():
                wallets_detail.append({
                    "type": wallet_type,
                    "balance_eur": 0,  # Not calculated per wallet, only total
                    "provider": wallet_data.get("provider", "manual")
                })
        
        return {
            "success": True,
            "entity_id": entity_id,
            "entity_name": entity.get("name"),
            "total_eur": round(total_eur, 2),
            "wallets": wallets_detail
        }
    
    @staticmethod
    def get_overview(user_id: str = None, owner_filter: str = None) -> Dict:
        """
        Totaal overzicht van alle entities
        
        Args:
            user_id: Voor crypto balances (optioneel)
            owner_filter: Filter op owner ("spark", "willem", None = all)
        
        Returns:
            {
                "success": true,
                "total_eur": 1234.56,
                "entities": [
                    {
                        "id": "spark_core",
                        "name": "Spark Core",
                        "icon": "🧠",
                        "balance_eur": 4.93,
                        "color": "blue"
                    },
                    ...
                ],
                "user_wallet": {...}  # If user_id provided
            }
        """
        entities = WalletService.get_entities()
        
        entities_list = []
        total_eur = 0.0
        
        for entity_id, entity_data in entities.items():
            # Filter op owner indien gegeven
            if owner_filter:
                entity_owner = entity_data.get("owner", "")
                if owner_filter == "spark" and entity_owner not in ["system", "spark_core"]:
                    continue
                elif owner_filter == "willem" and entity_owner != "willem":
                    continue
            
            # Bereken balance
            balance_result = WalletService.get_entity_balance(entity_id, user_id)
            
            if balance_result.get("success"):
                entity_balance = balance_result.get("total_eur", 0.0)
                total_eur += entity_balance
                
                entities_list.append({
                    "id": entity_id,
                    "name": entity_data.get("name"),
                    "icon": entity_data.get("icon"),
                    "type": entity_data.get("type"),
                    "description": entity_data.get("description"),
                    "balance_eur": entity_balance,
                    "color": entity_data.get("color"),
                    "wallets": balance_result.get("wallets", [])
                })
            else:
                # Entity has error (e.g., Bitvavo connection failed)
                # Don't add to total, show error state
                entities_list.append({
                    "id": entity_id,
                    "name": entity_data.get("name"),
                    "icon": entity_data.get("icon"),
                    "type": entity_data.get("type"),
                    "description": entity_data.get("description"),
                    "balance_eur": None,  # None = error state, niet €0
                    "color": entity_data.get("color"),
                    "error": balance_result.get("error", "Fout bij ophalen balance"),
                    "error_type": balance_result.get("error_type", "unknown")
                })
        
        result = {
            "success": True,
            "total_eur": round(total_eur, 2),
            "entities": entities_list
        }
        
        # Add user wallet als user_id gegeven
        if user_id:
            user_wallet = WalletService.get_user_wallet(user_id)
            if user_wallet:
                result["user_wallet"] = user_wallet
        
        return result

    @staticmethod
    def add_transaction(entity_id: str, amount: float, tx_type: str, description: str, user_id: str = None) -> Dict:
        """
        Voeg transaction toe aan entity
        
        Args:
            entity_id: Entity ID
            amount: Bedrag in EUR (positief getal)
            tx_type: Type transaction ("donation", "income", "expense")
            description: Korte beschrijving
            user_id: User die transaction toevoegt (optioneel)
        
        Returns:
            {"success": true, "transaction": {...}}
        """
        # Validate entity exists
        entity = WalletService.get_entity(entity_id)
        if not entity:
            return {"success": False, "error": "Entity not found"}
        
        # Validate type
        valid_types = ["donation", "income", "expense", "transfer"]
        if tx_type not in valid_types:
            return {"success": False, "error": f"Invalid type. Must be one of: {valid_types}"}
        
        # Validate amount
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        
        try:
            # Load transactions
            data = DataManager.load_data(WalletService.TRANSACTIONS_PATH)
            transactions = data.get("transactions", [])
            
            # Create new transaction
            transaction = {
                "id": f"tx_{uuid.uuid4().hex[:12]}",
                "entity_id": entity_id,
                "type": tx_type,
                "amount": round(amount, 2),
                "description": description,
                "timestamp": int(time.time()),
                "created_by": user_id or "system",
                "created_at": time.time()
            }
            
            transactions.append(transaction)
            
            # Save
            data["transactions"] = transactions
            DataManager.save_data(WalletService.TRANSACTIONS_PATH, data)
            
            return {
                "success": True,
                "transaction": transaction
            }
        
        except Exception as e:
            print(f"[WALLET] Error adding transaction: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_transactions(entity_id: str = None, limit: int = 100) -> Dict:
        """
        Haal transactions op
        
        Args:
            entity_id: Filter op entity (optioneel, None = alle transactions)
            limit: Max aantal transactions
        
        Returns:
            {"success": true, "transactions": [...], "stats": {...}}
        """
        try:
            data = DataManager.load_data(WalletService.TRANSACTIONS_PATH)
            transactions = data.get("transactions", [])
            
            # Filter op entity_id indien gegeven
            if entity_id:
                transactions = [tx for tx in transactions if tx.get("entity_id") == entity_id]
            
            # Sort by timestamp (newest first)
            transactions = sorted(transactions, key=lambda x: x.get("timestamp", 0), reverse=True)
            
            # Limit
            transactions = transactions[:limit]
            
            # Calculate stats
            total_donations = sum(tx["amount"] for tx in transactions if tx.get("type") == "donation")
            total_income = sum(tx["amount"] for tx in transactions if tx.get("type") == "income")
            total_expenses = sum(tx["amount"] for tx in transactions if tx.get("type") == "expense")
            
            return {
                "success": True,
                "transactions": transactions,
                "count": len(transactions),
                "stats": {
                    "total_donations": round(total_donations, 2),
                    "total_income": round(total_income, 2),
                    "total_expenses": round(total_expenses, 2),
                    "net": round(total_donations + total_income - total_expenses, 2)
                }
            }
        
        except Exception as e:
            print(f"[WALLET] Error loading transactions: {e}")
            return {"success": False, "error": str(e), "transactions": []}

            
            if balance_result.get("success"):
                entity_balance = balance_result.get("total_eur", 0.0)
                total_eur += entity_balance
                
                entities_list.append({
                    "id": entity_id,
                    "name": entity_data.get("name"),
                    "icon": entity_data.get("icon"),
                    "type": entity_data.get("type"),
                    "description": entity_data.get("description"),
                    "balance_eur": entity_balance,
                    "color": entity_data.get("color"),
                    "wallets": balance_result.get("wallets", [])
                })
        
        result = {
            "success": True,
            "total_eur": round(total_eur, 2),
            "entities": entities_list
        }
        
        # Add user wallet als user_id gegeven
        if user_id:
            user_wallet = WalletService.get_user_wallet(user_id)
            if user_wallet:
                result["user_wallet"] = user_wallet
        
        return result
