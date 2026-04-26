from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.encryption import verify_password, SECRET_KEY, ALGORITHM
from app.schema.user import TokenData
from app.models.user import User
from app.core.database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_public_id(db: Session, public_id: str) -> User | None:
    return db.query(User).filter(User.public_id == public_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        public_id: str | None = payload.get("sub")
        if public_id is None:
            raise credentials_exception
        token_data = TokenData(public_id=public_id)

    except JWTError:
        raise credentials_exception

    user = get_user_by_public_id(db, public_id=token_data.public_id)

    if user is None:
        raise credentials_exception
    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_optional_scheme),
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        public_id: str | None = payload.get("sub")
        if public_id is None:
            return None
    except JWTError:
        return None

    return get_user_by_public_id(db, public_id=public_id)