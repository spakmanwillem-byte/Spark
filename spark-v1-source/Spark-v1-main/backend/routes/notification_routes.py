"""
Notifications API Routes
=========================
Endpoints voor notificatie systeem
"""

from fastapi import APIRouter
from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/unread")
async def get_unread_notifications(user_id: str = "user-001"):
    """Get unread notifications voor user"""
    notifications = NotificationService.get_unread_notifications(user_id)
    return {
        "success": True,
        "count": len(notifications),
        "notifications": notifications
    }


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    result = NotificationService.mark_as_read(notification_id)
    return result


@router.post("/test")
async def send_test_notification():
    """Test endpoint - send demo notification"""
    result = NotificationService.send_trade_profit_alert(
        profit_eur=0.05,
        trade_data={"pot": 1, "price": 395.50, "test": True}
    )
    return result
