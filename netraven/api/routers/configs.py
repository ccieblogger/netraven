from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from netraven.db.session import get_db
from typing import List, Dict, Any

router = APIRouter(
    prefix="/api/configs",
    tags=["Configs"]
)

@router.get("/search", summary="Full-text search device configurations")
def search_configs(
    q: str = Query(..., description="Search query for configuration text"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Search device configuration snapshots using Postgres full-text search.
    Returns a list of matching snapshots with metadata and highlighted snippets.
    """
    sql = text("""
        SELECT id, device_id, config_data, config_metadata, retrieved_at,
               ts_headline('english', config_data, plainto_tsquery('english', :q)) AS snippet
        FROM device_configurations
        WHERE to_tsvector('english', config_data) @@ plainto_tsquery('english', :q)
        ORDER BY retrieved_at DESC
        LIMIT 50
    """)
    results = db.execute(sql, {"q": q}).fetchall()
    return [
        {
            "id": row.id,
            "device_id": row.device_id,
            "retrieved_at": row.retrieved_at,
            "snippet": row.snippet,
            "config_metadata": row.config_metadata
        }
        for row in results
    ]

@router.get("/{device_id}/history", summary="Get version history for a device")
def get_device_config_history(
    device_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all configuration snapshots for a device, ordered by retrieval time (descending).
    Returns metadata for each snapshot.
    """
    sql = text("""
        SELECT id, device_id, retrieved_at, config_metadata
        FROM device_configurations
        WHERE device_id = :device_id
        ORDER BY retrieved_at DESC
        LIMIT 100
    """)
    results = db.execute(sql, {"device_id": device_id}).fetchall()
    return [
        {
            "id": row.id,
            "device_id": row.device_id,
            "retrieved_at": row.retrieved_at,
            "config_metadata": row.config_metadata
        }
        for row in results
    ]

@router.get("/{config_id}", summary="Get a specific config snapshot by ID")
def get_config_snapshot(
    config_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve a specific configuration snapshot (raw config and metadata).
    """
    sql = text("""
        SELECT id, device_id, config_data, config_metadata, retrieved_at
        FROM device_configurations
        WHERE id = :config_id
        LIMIT 1
    """)
    row = db.execute(sql, {"config_id": config_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    return {
        "id": row.id,
        "device_id": row.device_id,
        "retrieved_at": row.retrieved_at,
        "config_metadata": row.config_metadata,
        "config_data": row.config_data
    }
