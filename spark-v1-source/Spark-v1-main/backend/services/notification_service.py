"""
Notification Service
====================
Stuurt notificaties naar gebruiker

Types:
- Trading winst/verlies alerts
- System events
- Important updates

Willem's wens: "bark yhee winst [amount]" bij winst trades
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

NOTIFICATIONS_FILE = Path("/app/backend/data/notifications.json")


class NotificationService:
    """
    Notification service voor trading alerts
    """
    
    @staticmethod
    def send_notification(
        type: str,
        title: str,
        message: str,
        data: dict = None,
        user_id: str = "user-001"
    ) -> Dict:
        """
        Stuur een notificatie
        
        Args:
            type: "success", "warning", "error", "info"
            title: Titel van notificatie
            message: Bericht
            data: Extra data (optional)
            user_id: User ID
        
        Returns:
            {"success": bool, "notification": dict}
        """
        notification = {
            "id": f"notif_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "user_id": user_id,
            "type": type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False
        }
        
        # Save to file
        try:
            # Load existing
            if NOTIFICATIONS_FILE.exists():
                with open(NOTIFICATIONS_FILE, 'r') as f:
                    notifications = json.load(f)
            else:
                notifications = []
            
            # Add new
            notifications.append(notification)
            
            # Keep last 100 only
            notifications = notifications[-100:]
            
            # Save
            with open(NOTIFICATIONS_FILE, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            logger.info(f"📬 Notification sent: {title}")
            
            return {
                "success": True,
                "notification": notification
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def send_trade_profit_alert(profit_eur: float, trade_data: dict = None) -> Dict:
        """
        Willem's special: "🎉 Yhee winst €X.XX!"
        
        Args:
            profit_eur: Winst in euros
            trade_data: Extra trade info (price, pot, etc)
        """
        return NotificationService.send_notification(
            type="success",
            title="🎉 Yhee Winst!",
            message=f"Trade succesvol! Winst: €{profit_eur:.2f}",
            data=trade_data or {}
        )
    
    @staticmethod
    def send_trade_loss_alert(loss_eur: float, trade_data: dict = None) -> Dict:
        """
        Willem's special: "😱 Damit oh nee! -€X.XX"
        (Komt niet voor, maar just in case)
        
        Args:
            loss_eur: Verlies in euros (positief getal)
            trade_data: Extra trade info
        """
        return NotificationService.send_notification(
            type="error",
            title="😱 Damit oh nee!",
            message=f"Trade verlies: -€{loss_eur:.2f}",
            data=trade_data or {}
        )
    
    @staticmethod
    def get_unread_notifications(user_id: str = "user-001") -> List[Dict]:
        """
        Get unread notifications voor user
        """
        try:
            if not NOTIFICATIONS_FILE.exists():
                return []
            
            with open(NOTIFICATIONS_FILE, 'r') as f:
                notifications = json.load(f)
            
            # Filter unread for user
            unread = [
                n for n in notifications
                if n.get("user_id") == user_id and not n.get("read", False)
            ]
            
            return unread
            
        except Exception as e:
            logger.error(f"❌ Failed to get notifications: {e}")
            return []
    
    @staticmethod
    def mark_as_read(notification_id: str) -> Dict:
        """Mark notification as read"""
        try:
            if not NOTIFICATIONS_FILE.exists():
                return {"success": False, "error": "No notifications"}
            
            with open(NOTIFICATIONS_FILE, 'r') as f:
                notifications = json.load(f)
            
            # Find and mark as read
            found = False
            for n in notifications:
                if n.get("id") == notification_id:
                    n["read"] = True
                    found = True
                    break
            
            if not found:
                return {"success": False, "error": "Notification not found"}
            
            # Save
            with open(NOTIFICATIONS_FILE, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ Failed to mark as read: {e}")
            return {"success": False, "error": str(e)}


# Quick test
if __name__ == "__main__":
    # Test notification
    result = NotificationService.send_trade_profit_alert(
        profit_eur=0.05,
        trade_data={"pot": 1, "price": 395.50}
    )
    print(f"✅ Test: {result}")
    
    # Get unread
    unread = NotificationService.get_unread_notifications()
    print(f"📬 Unread: {len(unread)}")
