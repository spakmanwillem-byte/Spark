"""
User Files Routes - Personal File Storage System
Supports: Photos, Videos, Audio, Documents
Features: Profile photo, File sharing, Encryption ready
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import mimetypes

router = APIRouter()

# Base directories
MEDIA_DIR = "/app/backend/data/media"
USERS_MEDIA_DIR = f"{MEDIA_DIR}/users"
SPARK_MEDIA_DIR = f"{MEDIA_DIR}/user-000"

# Ensure directories exist
os.makedirs(USERS_MEDIA_DIR, exist_ok=True)
os.makedirs(SPARK_MEDIA_DIR, exist_ok=True)

# File metadata storage
FILES_INDEX = "/app/backend/data/system/user_files_index.json"


class FileMetadata(BaseModel):
    id: str
    user_id: str
    filename: str
    original_name: str
    category: str  # photo, video, audio, document, other
    mime_type: str
    size: int  # bytes
    visibility: str  # private, shared, public
    is_profile_photo: bool
    description: Optional[str] = None
    tags: List[str] = []
    uploaded_at: str
    filepath: str


def load_files_index():
    """Load files index from JSON"""
    if os.path.exists(FILES_INDEX):
        with open(FILES_INDEX, 'r') as f:
            return json.load(f)
    return {"files": []}


def save_files_index(data):
    """Save files index to JSON"""
    with open(FILES_INDEX, 'w') as f:
        json.dump(data, f, indent=2)


def get_category_from_mime(mime_type: str) -> str:
    """Determine category from MIME type"""
    if mime_type.startswith('image/'):
        return 'photo'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type in ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain']:
        return 'document'
    else:
        return 'other'


def get_user_storage_path(user_id: str) -> str:
    """Get user's storage directory"""
    if user_id == 'user-000':
        return SPARK_MEDIA_DIR
    else:
        user_dir = os.path.join(USERS_MEDIA_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Query(...),
    visibility: str = Query('private'),  # private, shared, public
    description: Optional[str] = Query(None),
    tags: Optional[str] = Query(None)  # comma-separated
):
    """
    Upload a file to user's personal storage
    
    Args:
        file: File to upload
        user_id: Owner of the file
        visibility: private (only owner), shared (friends), public (everyone)
        description: Optional description
        tags: Comma-separated tags
    """
    try:
        # Get user storage path
        user_storage = get_user_storage_path(user_id)
        
        # Generate unique filename
        timestamp = datetime.now(timezone.utc).timestamp()
        unique_filename = f"{int(timestamp)}_{file.filename.replace(' ', '_')}"
        filepath = os.path.join(user_storage, unique_filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        category = get_category_from_mime(mime_type)
        
        # Load index
        index = load_files_index()
        files = index.get('files', [])
        
        # Create metadata
        file_id = f"file_{len(files) + 1}"
        metadata = {
            "id": file_id,
            "user_id": user_id,
            "filename": unique_filename,
            "original_name": file.filename,
            "category": category,
            "mime_type": mime_type,
            "size": file_size,
            "visibility": visibility,
            "is_profile_photo": False,
            "description": description,
            "tags": tags.split(',') if tags else [],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "filepath": filepath
        }
        
        files.append(metadata)
        index['files'] = files
        save_files_index(index)
        
        return {
            "success": True,
            "file": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files/list")
async def list_files(
    user_id: str = Query(...),
    requesting_user_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None)  # Filter by category
):
    """
    List files based on visibility rules:
    - Own files (all visibility levels)
    - Shared files from others
    - Public files
    - Spark (user-000) files (always public)
    """
    try:
        index = load_files_index()
        all_files = index.get('files', [])
        
        filtered_files = []
        
        for file in all_files:
            # Own files (all)
            if file['user_id'] == user_id:
                filtered_files.append(file)
            # Shared files
            elif file['visibility'] == 'shared' and requesting_user_id:
                filtered_files.append(file)
            # Public files
            elif file['visibility'] == 'public':
                filtered_files.append(file)
            # Spark system files (always public)
            elif file['user_id'] == 'user-000':
                filtered_files.append(file)
        
        # Filter by category if specified
        if category:
            filtered_files = [f for f in filtered_files if f['category'] == category]
        
        return {"files": filtered_files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/download/{file_id}")
async def download_file(
    file_id: str,
    user_id: Optional[str] = Query(None)
):
    """Download/stream a file"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        file_meta = next((f for f in files if f['id'] == file_id), None)
        
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check permissions
        if file_meta['visibility'] == 'private' and file_meta['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(file_meta['filepath']):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=file_meta['filepath'],
            filename=file_meta['original_name'],
            media_type=file_meta['mime_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Query(...)
):
    """Delete a file (only owner can delete)"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        file_meta = next((f for f in files if f['id'] == file_id), None)
        
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Only owner can delete
        if file_meta['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Only owner can delete")
        
        # Delete file from disk
        if os.path.exists(file_meta['filepath']):
            os.remove(file_meta['filepath'])
        
        # Remove from index
        files = [f for f in files if f['id'] != file_id]
        index['files'] = files
        save_files_index(index)
        
        return {"success": True, "message": "File deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/{file_id}/visibility")
async def update_visibility(
    file_id: str,
    visibility: str = Query(...),  # private, shared, public
    user_id: str = Query(...)
):
    """Update file visibility (only owner)"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        file_meta = next((f for f in files if f['id'] == file_id), None)
        
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Only owner can change visibility
        if file_meta['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Only owner can change visibility")
        
        # Update
        file_meta['visibility'] = visibility
        save_files_index(index)
        
        return {"success": True, "file": file_meta}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/{file_id}/set-profile-photo")
async def set_profile_photo(
    file_id: str,
    user_id: str = Query(...)
):
    """Set a photo as profile picture"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        file_meta = next((f for f in files if f['id'] == file_id), None)
        
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Only owner can set their profile photo
        if file_meta['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Must be a photo
        if file_meta['category'] != 'photo':
            raise HTTPException(status_code=400, detail="Only photos can be profile pictures")
        
        # Unset previous profile photo
        for f in files:
            if f['user_id'] == user_id and f['is_profile_photo']:
                f['is_profile_photo'] = False
        
        # Set new profile photo
        file_meta['is_profile_photo'] = True
        file_meta['visibility'] = 'public'  # Profile photos are always public
        
        save_files_index(index)
        
        return {"success": True, "file": file_meta}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/profile-photo/{user_id}")
async def get_profile_photo(user_id: str):
    """Get user's profile photo"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        profile_photo = next(
            (f for f in files if f['user_id'] == user_id and f['is_profile_photo']),
            None
        )
        
        if not profile_photo:
            return {"profile_photo": None}
        
        return {"profile_photo": profile_photo}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/stats/{user_id}")
async def get_storage_stats(user_id: str):
    """Get user's storage statistics"""
    try:
        index = load_files_index()
        files = index.get('files', [])
        
        user_files = [f for f in files if f['user_id'] == user_id]
        
        total_size = sum(f['size'] for f in user_files)
        
        stats = {
            "total_files": len(user_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_category": {}
        }
        
        # Count by category
        for category in ['photo', 'video', 'audio', 'document', 'other']:
            cat_files = [f for f in user_files if f['category'] == category]
            stats['by_category'][category] = {
                "count": len(cat_files),
                "size": sum(f['size'] for f in cat_files)
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/user/data/download/{user_id}/{filename}")
async def download_personal_data(user_id: str, filename: str):
    """
    Download personal JSON data (dagboek, agenda, etc)
    """
    try:
        # Security: only allow specific filenames
        allowed_files = [
            'dagboek.json', 'agenda.json', 'relationships.json',
            'expenses.json', 'income.json', 'achievements.json', 'settings.json'
        ]
        
        if filename not in allowed_files:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = f"/app/backend/data/users/{user_id}/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            file_path,
            media_type='application/json',
            filename=f"{user_id}_{filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
