from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, authenticate_user, get_user
from app.core.encryption import create_access_token, get_password_hash, verify_password
from app.schema.user import Token
from app.schema.user import RegisterRequest, UserResponse, LoginRequest   
from app.models.user import User

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(user_login: LoginRequest, db: Session = Depends(get_db)):
    user = get_user(db, username=user_login.identifier)
    if not user:
        user = db.query(User).filter(User.email == user_login.identifier).first()
    
    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=Token)
def signup(user: RegisterRequest, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}