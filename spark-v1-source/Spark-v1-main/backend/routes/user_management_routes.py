"""
User Management Routes - Admin only
Delete, block, warn users
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict
import json
from datetime import datetime

router = APIRouter()

USERS_FILE = "/app/backend/data/system/users.json"


def load_users():
    """Load users from JSON"""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except Exception as e:
        print(f"Error loading users: {e}")
        return []


def save_users(users):
    """Save users to JSON"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump({'users': users}, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


@router.get("/list")
async def list_users(admin_user_id: str = Query(...)):
    """
    List all users (admin only)
    """
    users = load_users()
    
    # Check if requester is admin (gradatie 1)
    admin = next((u for u in users if u['id'] == admin_user_id), None)
    if not admin or admin.get('gradatie', 99) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return users with key info
    user_list = []
    for user in users:
        user_list.append({
            'id': user['id'],
            'naam': user.get('naam', 'N/A'),
            'volledige_naam': user.get('volledige_naam', ''),
            'gradatie': user.get('gradatie', 99),
            'rol': user.get('rol', ''),
            'registered_date': user.get('registered_date', ''),
            'last_active': user.get('last_active', ''),
            'gesprekken_count': user.get('gesprekken_count', 0),
            'blocked': user.get('blocked', False),
            'blocked_reason': user.get('blocked_reason', ''),
            'warnings': user.get('warnings', [])
        })
    
    return {
        'success': True,
        'users': user_list,
        'total': len(user_list)
    }


@router.post("/block")
async def block_user(
    admin_user_id: str = Query(...),
    target_user_id: str = Query(...),
    reason: str = Query(...)
):
    """
    Block a user (admin only)
    """
    users = load_users()
    
    # Check admin
    admin = next((u for u in users if u['id'] == admin_user_id), None)
    if not admin or admin.get('gradatie', 99) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find target user
    target = next((u for u in users if u['id'] == target_user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't block gradatie 1 (admin)
    if target.get('gradatie', 99) == 1:
        raise HTTPException(status_code=403, detail="Cannot block admin users")
    
    # Block user
    target['blocked'] = True
    target['blocked_reason'] = reason
    target['blocked_at'] = datetime.now().isoformat()
    target['blocked_by'] = admin_user_id
    
    if save_users(users):
        return {
            'success': True,
            'message': f"User {target['naam']} blocked"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save changes")


@router.post("/unblock")
async def unblock_user(
    admin_user_id: str = Query(...),
    target_user_id: str = Query(...)
):
    """
    Unblock a user (admin only)
    """
    users = load_users()
    
    # Check admin
    admin = next((u for u in users if u['id'] == admin_user_id), None)
    if not admin or admin.get('gradatie', 99) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find target user
    target = next((u for u in users if u['id'] == target_user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Unblock
    target['blocked'] = False
    target['blocked_reason'] = ''
    target['unblocked_at'] = datetime.now().isoformat()
    target['unblocked_by'] = admin_user_id
    
    if save_users(users):
        return {
            'success': True,
            'message': f"User {target['naam']} unblocked"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save changes")


@router.post("/warn")
async def warn_user(
    admin_user_id: str = Query(...),
    target_user_id: str = Query(...),
    warning: str = Query(...)
):
    """
    Add a warning to a user (admin only)
    """
    users = load_users()
    
    # Check admin
    admin = next((u for u in users if u['id'] == admin_user_id), None)
    if not admin or admin.get('gradatie', 99) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find target user
    target = next((u for u in users if u['id'] == target_user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add warning
    if 'warnings' not in target:
        target['warnings'] = []
    
    target['warnings'].append({
        'warning': warning,
        'timestamp': datetime.now().isoformat(),
        'issued_by': admin_user_id
    })
    
    if save_users(users):
        return {
            'success': True,
            'message': f"Warning added to {target['naam']}",
            'total_warnings': len(target['warnings'])
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save changes")


@router.delete("/delete")
async def delete_user(
    admin_user_id: str = Query(...),
    target_user_id: str = Query(...),
    confirmation: str = Query(...)
):
    """
    DELETE a user permanently (admin only)
    Requires confirmation = user's name
    """
    users = load_users()
    
    # Check admin
    admin = next((u for u in users if u['id'] == admin_user_id), None)
    if not admin or admin.get('gradatie', 99) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find target user
    target = next((u for u in users if u['id'] == target_user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't delete gradatie 1 (admin)
    if target.get('gradatie', 99) == 1:
        raise HTTPException(status_code=403, detail="Cannot delete admin users")
    
    # Confirmation check
    if confirmation != target.get('naam', ''):
        raise HTTPException(status_code=400, detail="Confirmation name does not match")
    
    # Remove user
    users = [u for u in users if u['id'] != target_user_id]
    
    if save_users(users):
        return {
            'success': True,
            'message': f"User {target['naam']} permanently deleted"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save changes")
