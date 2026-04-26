import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import authenticate_user, get_db, get_user_by_email, get_user_by_public_id
from app.core.encryption import create_access_token, get_password_hash
from app.schema.user import Token
from app.schema.user import LoginRequest, RegisterRequest
from app.models.user import User

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(user_login: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, email=user_login.email, password=user_login.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.public_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=Token)
def signup(user: RegisterRequest, db: Session = Depends(get_db)):
    db_email = get_user_by_email(db, email=user.email)
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    public_id = secrets.token_hex(16)
    while get_user_by_public_id(db, public_id=public_id):
        public_id = secrets.token_hex(16)

    db_user = User(public_id=public_id, email=user.email, password=hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": db_user.public_id})
    return {"access_token": access_token, "token_type": "bearer"}