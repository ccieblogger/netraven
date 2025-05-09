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
