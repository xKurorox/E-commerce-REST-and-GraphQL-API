from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session
from app.database import get_db
import os
from app.models import User

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Tells FastAPI where clients send their token to authenticate; used to extract the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the JWT and verify it was signed with our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired, please log in again")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Extract the user id stored in the token's "sub" (subject) field
    user_id = int(payload.get("sub"))

    # Look up the user in the database to make sure they still exist
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
