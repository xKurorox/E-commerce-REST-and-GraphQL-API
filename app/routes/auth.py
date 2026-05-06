from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.pydantic_schemas import UserCreate, UserLogin, UserResponse, Token
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# bcrypt is the hashing algorithm; "deprecated=auto" automatically upgrades old hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    # Set the token's expiry time
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Sign the token with our secret key so it can't be tampered with
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Block duplicate emails
    user_entry = db.query(User).filter(User.email == user.email).first()
    if user_entry:
        raise HTTPException(status_code=409, detail="User already exist")
    hashed_password = hash_password(user.password)
    new_user = User(name=user.name, hashed_password=hashed_password, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    user_entry = db.query(User).filter(User.email == user.email).first()
    if not user_entry:
        raise HTTPException(status_code=404, detail="Email was not found")
    if verify_password(user.password, user_entry.hashed_password):
        # Embed user id and admin flag in the token so routes can check permissions without a DB hit
        access_token = create_access_token(data={"sub": str(user_entry.id), "is_admin": user_entry.is_admin})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
