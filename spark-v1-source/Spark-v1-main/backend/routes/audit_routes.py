"""
Audit Routes - Self-Check API
==============================
Spark kan zichzelf auditen via API

Endpoints:
- GET /api/audit/placeholders - Lege action placeholders
- GET /api/audit/weak-triggers - Triggers zonder goede response
- GET /api/audit/weak-verbanden - Zwakke verbanden (1 veld overlap)
- GET /api/audit/missing-5wh - Cards zonder 5W+H
- GET /api/audit/full - Complete audit
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import sys
sys.path.append('/app/backend')

from services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/placeholders")
async def get_placeholder_actions():
    """
    📋 Scan lege acties (placeholders)
    
    Vind alle action cards die nog niet geïmplementeerd zijn
    """
    try:
        service = AuditService()
        placeholders = service.scan_placeholder_actions()
        
        return {
            "success": True,
            "count": len(placeholders),
            "placeholders": placeholders,
            "message": f"Found {len(placeholders)} placeholder actions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weak-triggers")
async def get_weak_triggers():
    """
    ⚠️ Scan triggers zonder goede response
    
    Vind greeting/action cards met lege of te simpele responses
    """
    try:
        service = AuditService()
        weak = service.scan_weak_triggers()
        
        return {
            "success": True,
            "count": len(weak),
            "weak_triggers": weak,
            "message": f"Found {len(weak)} weak triggers that need improvement"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weak-verbanden")
async def get_weak_verbanden(min_overlap: int = 2, limit: int = 20):
    """
    🔗 Scan zwakke verbanden
    
    Vind cards met weinig overlap (mogelijk ruis)
    
    Args:
        min_overlap: Minimaal aantal velden (default 2)
        limit: Max aantal resultaten (default 20)
    """
    try:
        service = AuditService()
        weak = service.scan_weak_verbanden(min_overlap=min_overlap)
        
        # Limit results
        weak = weak[:limit]
        
        return {
            "success": True,
            "count": len(weak),
            "min_overlap_threshold": min_overlap,
            "weak_verbanden": weak,
            "message": f"Found {len(weak)} cards met zwakke verbanden (< {min_overlap} velden overlap)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/missing-5wh")
async def get_missing_5wh(limit: int = 50):
    """
    📝 Scan cards zonder 5W+H
    
    Vind cards waar context nog niet ingevuld is
    
    Args:
        limit: Max aantal resultaten (default 50)
    """
    try:
        service = AuditService()
        missing = service.scan_missing_5wh()
        
        return {
            "success": True,
            "total_count": len(missing),
            "sample_count": min(len(missing), limit),
            "missing_5wh": missing[:limit],
            "message": f"Found {len(missing)} cards zonder 5W+H context"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full")
async def get_full_audit():
    """
    🔍 Complete audit
    
    Run alle scans en geef overzicht van:
    - Placeholder actions
    - Weak triggers
    - Weak verbanden
    - Missing 5W+H
    - Summary stats
    """
    try:
        service = AuditService()
        audit = service.run_full_audit()
        
        return {
            "success": True,
            "audit": audit,
            "message": "Full audit complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_audit_summary():
    """
    📊 Quick summary
    
    Alleen de cijfers, geen details
    """
    try:
        service = AuditService()
        audit = service.run_full_audit()
        
        return {
            "success": True,
            "summary": audit['summary'],
            "message": "Audit summary"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
