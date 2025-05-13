from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from netraven.db.session import get_db
from typing import List, Dict, Any
import difflib

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

@router.get("/diff", summary="Get unified diff between two config snapshots")
def diff_config_snapshots(
    config_id_a: int = Query(..., description="ID of the first config snapshot"),
    config_id_b: int = Query(..., description="ID of the second config snapshot"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Return a unified diff between two config snapshots' config_data fields.
    """
    sql = text("""
        SELECT id, config_data FROM device_configurations WHERE id = :id
    """)
    row_a = db.execute(sql, {"id": config_id_a}).fetchone()
    row_b = db.execute(sql, {"id": config_id_b}).fetchone()
    if not row_a or not row_b:
        raise HTTPException(status_code=404, detail="One or both config snapshots not found")
    a_lines = row_a.config_data.splitlines(keepends=True)
    b_lines = row_b.config_data.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        a_lines, b_lines,
        fromfile=f"config_{row_a.id}",
        tofile=f"config_{row_b.id}",
        lineterm=''  # No extra newlines
    ))
    return {
        "config_id_a": row_a.id,
        "config_id_b": row_b.id,
        "diff": diff
    }

@router.get("/list", summary="List all config snapshots")
def list_configs(
    device_id: int = Query(None, description="Filter by device ID"),
    start: int = Query(0, description="Offset for pagination"),
    limit: int = Query(50, description="Max results to return"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all configuration snapshots, optionally filtered by device_id, paginated.
    """
    sql = text("""
        SELECT id, device_id, retrieved_at, config_metadata
        FROM device_configurations
        WHERE (:device_id IS NULL OR device_id = :device_id)
        ORDER BY retrieved_at DESC
        OFFSET :start LIMIT :limit
    """)
    results = db.execute(sql, {"device_id": device_id, "start": start, "limit": limit}).fetchall()
    return [
        {
            "id": row.id,
            "device_id": row.device_id,
            "retrieved_at": row.retrieved_at,
            "config_metadata": row.config_metadata
        }
        for row in results
    ]

@router.delete("/{config_id}", summary="Delete a config snapshot by ID")
def delete_config_snapshot(
    config_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a specific configuration snapshot by ID.
    """
    sql = text("""
        DELETE FROM device_configurations WHERE id = :config_id RETURNING id
    """)
    result = db.execute(sql, {"config_id": config_id})
    db.commit()
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    return {"deleted_id": row.id}

@router.post("/{config_id}/restore", summary="Restore a config snapshot (mark as restored)")
def restore_config_snapshot(
    config_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mark a config as restored (optionally, create a new snapshot or update device state).
    For now, just log/return the action (actual device push is out of scope).
    """
    sql = text("""
        SELECT id, device_id, config_data, config_metadata, retrieved_at
        FROM device_configurations WHERE id = :config_id
    """)
    row = db.execute(sql, {"config_id": config_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    # In a real system, this would push config_data to the device.
    # Here, we just log/return the action.
    return {
        "restored_id": row.id,
        "device_id": row.device_id,
        "restored_at": row.retrieved_at,
        "message": "Config marked as restored (no device push performed)"
    }
