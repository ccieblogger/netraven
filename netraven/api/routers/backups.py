from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from netraven.db.session import get_db  # Corrected import path

router = APIRouter(
    prefix="/api/backups",
    tags=["Backups"]
)

@router.get("/count", summary="Get the count of backup configuration files")
def get_backup_count(db: Session = Depends(get_db)):
    """Retrieve the total number of backup configuration files."""
    count = db.execute("SELECT COUNT(*) FROM device_configurations").scalar()
    return {"count": count}
