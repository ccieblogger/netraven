from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session

from netraven.api import auth, schemas, models # Import models too
from netraven.api.dependencies import get_db_session # Import DB dependency

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Helper function (could be moved to auth.py or a crud layer)
def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/token", response_model=schemas.token.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    """Provides an access token for valid username/password.
    Uses OAuth2PasswordRequestForm for standard form data input.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, # Include role in token
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
