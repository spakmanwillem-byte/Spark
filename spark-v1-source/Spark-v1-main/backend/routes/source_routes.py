from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
import shutil
import uuid

router = APIRouter()

SOURCES_DIR = Path("/app/backend/data/sources")
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

class Source(BaseModel):
    id: str
    type: str  # 'pdf', 'audio', 'video', 'url'
    titel: str
    bestand: Optional[str] = None
    url: Optional[str] = None
    uploaded_at: str
    uploaded_by: str

@router.post("/upload")
async def upload_source(file: UploadFile = File(...), user_id: str = "user-001", titel: Optional[str] = None):
    """
    Upload PDF/audio/video source
    PLACEHOLDER: Currently saves file, full integration coming soon
    """
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        filepath = SOURCES_DIR / filename
        
        # Save file
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Determine type
        if file_ext.lower() in ['.pdf']:
            source_type = 'pdf'
        elif file_ext.lower() in ['.mp3', '.wav', '.ogg', '.m4a']:
            source_type = 'audio'
        elif file_ext.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
            source_type = 'video'
        else:
            source_type = 'file'
        
        source = {
            "id": file_id,
            "type": source_type,
            "titel": titel or file.filename,
            "bestand": filename,
            "uploaded_at": str(Path(filepath).stat().st_mtime),
            "uploaded_by": user_id,
            "file_size": Path(filepath).stat().st_size
        }
        
        return {
            "success": True,
            "message": "✅ Bestand geüpload! Link nu aan kenniskaarten.",
            "source": source,
            "note": "PLACEHOLDER: OCR en auto-kaart generatie komt binnenkort"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link")
async def link_source_to_card(source_id: str, card_id: str, pagina: Optional[int] = None):
    """Link source to knowledge card"""
    try:
        kb_file = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_file, 'r') as f:
            kb_data = json.load(f)
        
        entries = kb_data.get("knowledge_entries", [])
        card = next((e for e in entries if e["id"] == card_id), None)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Add source to bronnen array
        if "bronnen" not in card:
            card["bronnen"] = []
        
        # Check if already linked
        if any(b.get("id") == source_id for b in card["bronnen"]):
            return {"success": True, "message": "Bron al gekoppeld"}
        
        card["bronnen"].append({
            "id": source_id,
            "pagina": pagina
        })
        
        # Save
        with open(kb_file, 'w') as f:
            json.dump(kb_data, f, indent=2)
        
        return {"success": True, "message": "Bron gekoppeld aan kaart"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_sources():
    """Get all uploaded sources"""
    try:
        sources = []
        for file in SOURCES_DIR.glob("*"):
            if file.is_file():
                sources.append({
                    "filename": file.name,
                    "size": file.stat().st_size,
                    "uploaded_at": file.stat().st_mtime
                })
        
        return {"success": True, "sources": sources, "count": len(sources)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
