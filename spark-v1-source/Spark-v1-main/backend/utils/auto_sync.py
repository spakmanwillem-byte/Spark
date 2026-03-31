"""
Auto-Sync Wrapper voor Knowledge Base Updates

Zorgt ervoor dat nodes.json ALTIJD in sync blijft met knowledge_base.json

Usage:
    from utils.auto_sync import trigger_graph_sync
    
    # Na elke knowledge_base.json update:
    trigger_graph_sync()
"""

import logging
from typing import Optional
import asyncio
from services.knowledge_to_graph_sync import KnowledgeToGraphSync

logger = logging.getLogger(__name__)


class AutoSyncManager:
    """Manager voor automatische graph synchronisatie"""
    
    _sync_in_progress = False
    _pending_sync = False
    
    @classmethod
    def trigger_sync(cls, background: bool = True) -> Optional[dict]:
        """
        Trigger graph sync
        
        Args:
            background: Run in background (non-blocking) or foreground
            
        Returns:
            Sync result dict if foreground, None if background
        """
        if cls._sync_in_progress:
            logger.info("Sync already in progress, marking for re-sync after completion")
            cls._pending_sync = True
            return None
        
        if background:
            # Run in background (non-blocking)
            import threading
            thread = threading.Thread(target=cls._run_sync)
            thread.daemon = True
            thread.start()
            logger.info("🔄 Graph sync triggered in background")
            return None
        else:
            # Run in foreground (blocking)
            return cls._run_sync()
    
    @classmethod
    def _run_sync(cls) -> dict:
        """Internal sync runner"""
        cls._sync_in_progress = True
        
        try:
            logger.info("📚 Syncing knowledge_base.json → nodes.json...")
            
            result = KnowledgeToGraphSync.sync_knowledge_to_graph(
                generate_edges=True,
                verbose=False
            )
            
            logger.info(f"✅ Sync complete: {result['nodes_created']} nodes, {result['edges_created']} edges")
            
            # Check if another sync was requested while this one was running
            if cls._pending_sync:
                logger.info("Re-running sync due to pending request...")
                cls._pending_sync = False
                return cls._run_sync()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Graph sync failed: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            cls._sync_in_progress = False
    
    @classmethod
    def sync_on_startup(cls):
        """Run sync on server startup (non-blocking)"""
        logger.info("🚀 Running startup sync in background: knowledge_base.json → nodes.json")
        # Run in background to avoid blocking uvicorn startup
        cls.trigger_sync(background=True)
        logger.info("✅ Startup sync triggered (running in background)")


# Convenience function
def trigger_graph_sync(background: bool = True):
    """
    Convenience function to trigger graph sync
    
    Usage:
        from utils.auto_sync import trigger_graph_sync
        trigger_graph_sync()
    """
    return AutoSyncManager.trigger_sync(background=background)


def sync_on_startup():
    """Run sync on server startup"""
    AutoSyncManager.sync_on_startup()
