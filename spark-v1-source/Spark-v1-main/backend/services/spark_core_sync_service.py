"""
Spark Core Balance Sync Service
Periodically syncs Bitvavo balance to spark_core_balance.json
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional
from services.bitvavo_service import BitvavoService
from utils.logger import SparkLogger

SPARK_CORE_BALANCE_FILE = "/app/backend/data/financial/spark_core_balance.json"


class SparkCoreSyncService:
    """
    Background service voor het syncen van Spark Core Bitvavo balance
    """
    
    @staticmethod
    def load_config() -> Dict:
        """Load sync configuration from spark_core_balance.json"""
        try:
            if os.path.exists(SPARK_CORE_BALANCE_FILE):
                with open(SPARK_CORE_BALANCE_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            SparkLogger.log_system_event(f"[SYNC] Error loading config: {e}")
            return {}
    
    @staticmethod
    def save_config(config: Dict):
        """Save updated configuration"""
        try:
            os.makedirs(os.path.dirname(SPARK_CORE_BALANCE_FILE), exist_ok=True)
            with open(SPARK_CORE_BALANCE_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            SparkLogger.log_system_event("[SYNC] Configuration saved")
        except Exception as e:
            SparkLogger.log_system_event(f"[SYNC] Error saving config: {e}")
    
    @staticmethod
    def sync_bitvavo_balance() -> Dict:
        """
        Main sync function - haalt Bitvavo balance op en update config
        
        Returns:
            {
                "success": bool,
                "balance_eur": float,
                "message": str,
                "timestamp": str
            }
        """
        try:
            SparkLogger.log_system_event("[SYNC] Starting Bitvavo balance sync...")
            
            # Load current config
            config = SparkCoreSyncService.load_config()
            
            # Get Spark Core user_id from config (default: user-000)
            spark_user_id = config.get('sync', {}).get('spark_user_id', 'user-000')
            
            # Check if auto_sync is enabled
            auto_sync = config.get('sync', {}).get('auto_sync', False)
            
            if not auto_sync:
                SparkLogger.log_system_event("[SYNC] Auto-sync is disabled, skipping...")
                return {
                    "success": False,
                    "message": "Auto-sync is disabled",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Fetch Bitvavo balance
            SparkLogger.log_system_event(f"[SYNC] Fetching Bitvavo balance for {spark_user_id}...")
            balance_result = BitvavoService.get_balance(spark_user_id)
            
            if not balance_result.get('success'):
                error_msg = balance_result.get('error', 'Unknown error')
                SparkLogger.log_system_event(f"[SYNC] ❌ Failed to fetch balance: {error_msg}")
                
                # Update last_sync_attempt in config
                if 'sync' not in config:
                    config['sync'] = {}
                config['sync']['last_sync_attempt'] = datetime.now(timezone.utc).isoformat()
                config['sync']['last_sync_status'] = 'failed'
                config['sync']['last_sync_error'] = error_msg
                SparkCoreSyncService.save_config(config)
                
                return {
                    "success": False,
                    "message": f"Failed to fetch Bitvavo balance: {error_msg}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Extract total EUR value
            total_eur = balance_result.get('total_eur', 0.0)
            
            SparkLogger.log_system_event(f"[SYNC] ✅ Fetched balance: €{total_eur:.2f}")
            
            # Update config with new balance
            if 'spark_core' not in config:
                config['spark_core'] = {}
            
            old_balance = config['spark_core'].get('balance_eur', 0)
            config['spark_core']['balance_eur'] = round(total_eur, 2)
            config['spark_core']['last_updated'] = datetime.now(timezone.utc).isoformat()
            config['spark_core']['source'] = 'bitvavo_auto_sync'
            
            # Update sync status
            if 'sync' not in config:
                config['sync'] = {}
            config['sync']['last_sync_success'] = datetime.now(timezone.utc).isoformat()
            config['sync']['last_sync_status'] = 'success'
            config['sync']['last_sync_error'] = None
            
            # Save updated config
            SparkCoreSyncService.save_config(config)
            
            # Log balance change
            balance_change = total_eur - old_balance
            change_sign = '+' if balance_change >= 0 else ''
            SparkLogger.log_system_event(
                f"[SYNC] 💰 Balance updated: €{old_balance:.2f} → €{total_eur:.2f} ({change_sign}€{balance_change:.2f})"
            )
            
            return {
                "success": True,
                "balance_eur": total_eur,
                "old_balance": old_balance,
                "change": balance_change,
                "message": f"Balance synced successfully: €{total_eur:.2f}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during sync: {str(e)}"
            SparkLogger.log_system_event(f"[SYNC] ❌ {error_msg}")
            
            # Update error in config
            config = SparkCoreSyncService.load_config()
            if 'sync' not in config:
                config['sync'] = {}
            config['sync']['last_sync_attempt'] = datetime.now(timezone.utc).isoformat()
            config['sync']['last_sync_status'] = 'error'
            config['sync']['last_sync_error'] = error_msg
            SparkCoreSyncService.save_config(config)
            
            return {
                "success": False,
                "message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @staticmethod
    def get_sync_status() -> Dict:
        """
        Get current sync status and configuration
        
        Returns:
            {
                "auto_sync": bool,
                "interval_minutes": int,
                "last_sync_success": str (ISO timestamp),
                "last_sync_status": str,
                "current_balance": float,
                "last_updated": str
            }
        """
        config = SparkCoreSyncService.load_config()
        
        return {
            "auto_sync": config.get('sync', {}).get('auto_sync', False),
            "interval_minutes": config.get('sync', {}).get('sync_interval_minutes', 30),
            "spark_user_id": config.get('sync', {}).get('spark_user_id', 'user-000'),
            "last_sync_success": config.get('sync', {}).get('last_sync_success'),
            "last_sync_attempt": config.get('sync', {}).get('last_sync_attempt'),
            "last_sync_status": config.get('sync', {}).get('last_sync_status'),
            "last_sync_error": config.get('sync', {}).get('last_sync_error'),
            "current_balance": config.get('spark_core', {}).get('balance_eur', 0),
            "last_updated": config.get('spark_core', {}).get('last_updated'),
            "source": config.get('spark_core', {}).get('source', 'manual')
        }
    
    @staticmethod
    def enable_auto_sync(
        interval_minutes: int = 30,
        spark_user_id: str = 'user-000'
    ) -> Dict:
        """
        Enable automatic syncing
        
        Args:
            interval_minutes: Sync interval (default: 30)
            spark_user_id: User ID for Spark Core Bitvavo account (default: user-000)
        
        Returns:
            Updated configuration
        """
        config = SparkCoreSyncService.load_config()
        
        if 'sync' not in config:
            config['sync'] = {}
        
        config['sync']['auto_sync'] = True
        config['sync']['sync_interval_minutes'] = interval_minutes
        config['sync']['spark_user_id'] = spark_user_id
        config['sync']['enabled_at'] = datetime.now(timezone.utc).isoformat()
        
        SparkCoreSyncService.save_config(config)
        
        SparkLogger.log_system_event(
            f"[SYNC] ✅ Auto-sync enabled: {interval_minutes} min interval, user: {spark_user_id}"
        )
        
        return config
    
    @staticmethod
    def disable_auto_sync() -> Dict:
        """
        Disable automatic syncing
        
        Returns:
            Updated configuration
        """
        config = SparkCoreSyncService.load_config()
        
        if 'sync' not in config:
            config['sync'] = {}
        
        config['sync']['auto_sync'] = False
        config['sync']['disabled_at'] = datetime.now(timezone.utc).isoformat()
        
        SparkCoreSyncService.save_config(config)
        
        SparkLogger.log_system_event("[SYNC] ⏸️ Auto-sync disabled")
        
        return config
    
    @staticmethod
    def manual_sync() -> Dict:
        """
        Manually trigger a sync (works even if auto_sync is disabled)
        
        Returns:
            Sync result
        """
        SparkLogger.log_system_event("[SYNC] Manual sync triggered")
        
        # Temporarily enable auto_sync for this call
        config = SparkCoreSyncService.load_config()
        original_auto_sync = config.get('sync', {}).get('auto_sync', False)
        
        if not original_auto_sync:
            config['sync']['auto_sync'] = True
            SparkCoreSyncService.save_config(config)
        
        # Run sync
        result = SparkCoreSyncService.sync_bitvavo_balance()
        
        # Restore original setting
        if not original_auto_sync:
            config['sync']['auto_sync'] = False
            SparkCoreSyncService.save_config(config)
        
        return result
