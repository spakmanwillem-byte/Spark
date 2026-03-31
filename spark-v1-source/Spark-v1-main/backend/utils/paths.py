"""
Cross-platform Path Helper
Provides platform-independent path construction for Windows, Linux, and Odroid
"""
import os
from pathlib import Path

# Base directory - resolve once at module load
BACKEND_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BACKEND_DIR / "data"

def get_data_path(*parts):
    """
    Construct cross-platform path within data directory
    
    Args:
        *parts: Path components (e.g., "users", "user-001", "settings.json")
    
    Returns:
        Path: Cross-platform Path object
    
    Example:
        >>> get_data_path("users", "user-001", "settings.json")
        Path("/app/backend/data/users/user-001/settings.json")  # Linux
        Path("C:\\app\\backend\\data\\users\\user-001\\settings.json")  # Windows
    """
    return DATA_DIR.joinpath(*parts)

def get_backend_path(*parts):
    """
    Construct cross-platform path within backend directory
    
    Args:
        *parts: Path components
    
    Returns:
        Path: Cross-platform Path object
    """
    return BACKEND_DIR.joinpath(*parts)

# Common data paths (pre-constructed for convenience)
PATHS = {
    # System
    "action_log": get_data_path("system", "action_log.json"),
    "decision_log": get_data_path("system", "decision_log.json"),
    "settings": get_data_path("system", "settings.json"),
    "logs": get_data_path("system", "logs.json"),
    "bug_reports": get_data_path("system", "bug_reports.json"),
    "user_files_index": get_data_path("system", "user_files_index.json"),
    "trading_context_cache": get_data_path("system", "trading_context_cache.json"),
    
    # Knowledge
    "knowledge_base": get_data_path("learned_knowledge", "knowledge_base.json"),
    
    # Graph
    "graph_nodes": get_data_path("graph", "nodes.json"),
    "graph_edges": get_data_path("graph", "edges.json"),
    "graph_metadata": get_data_path("graph", "metadata.json"),
    
    # Financial
    "transactions": get_data_path("financial", "transactions.json"),
    "spark_core_balance": get_data_path("financial", "spark_core_balance.json"),
    
    # Game
    "world_save": get_data_path("world_save.json"),
    "custom_buildings": get_data_path("custom_buildings.json"),
    "custom_resources": get_data_path("custom_resources.json"),
    "task_actions": get_data_path("task_actions.json"),
    "bot_blueprints": get_data_path("bot_blueprints.json"),
    "notifications": get_data_path("notifications.json"),
    
    # Community
    "community_messages": get_data_path("community", "messages.json"),
    
    # Directories
    "media_dir": get_data_path("media"),
    "sounds_dir": get_data_path("media", "sounds"),
    "persons_dir": get_data_path("persons"),
    "emotions_dir": get_data_path("emotions"),
    "replay_logs_dir": get_data_path("wallet", "replay_logs"),
    "backtesting_dir": get_data_path("backtesting"),
    "bots_dir": get_data_path("bots"),
    "live_trading_dir": get_data_path("live_trading"),
}

def get_user_path(user_id, *parts):
    """
    Construct cross-platform path for user-specific data
    
    Args:
        user_id: User ID (e.g., "001" or "user-001")
        *parts: Additional path components
    
    Returns:
        Path: Cross-platform Path object
    
    Example:
        >>> get_user_path("001", "settings.json")
        Path("/app/backend/data/users/user-001/settings.json")
    """
    # Normalize user ID (add "user-" prefix if not present)
    if not user_id.startswith("user-"):
        user_id = f"user-{user_id}"
    
    return get_data_path("users", user_id, *parts)

def get_live_trading_path(user_id, *parts):
    """
    Construct cross-platform path for live trading data
    
    Args:
        user_id: User ID
        *parts: Additional path components (e.g., "runs", "run_id", "position_state.json")
    
    Returns:
        Path: Cross-platform Path object
    """
    if not user_id.startswith("user-"):
        user_id = f"user-{user_id}"
    
    return get_data_path("live_trading", user_id, *parts)

# Export for convenience
__all__ = [
    "BACKEND_DIR",
    "DATA_DIR",
    "PATHS",
    "get_data_path",
    "get_backend_path",
    "get_user_path",
    "get_live_trading_path",
]
