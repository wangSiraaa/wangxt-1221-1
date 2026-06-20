from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    return user


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from app.auth import verify_password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "密码修改成功"}
