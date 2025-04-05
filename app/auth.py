from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from .config import settings
import random
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

otp_storage = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_otp(length: int = 6) -> str:
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def store_otp(email: str, otp: str, expires_in: int = 300):
    expiration = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    otp_storage[email] = {"otp": otp, "expires": expiration}

def verify_otp(email: str, otp: str) -> bool:
    if email not in otp_storage:
        return False
    
    stored = otp_storage[email]
    if datetime.now(timezone.utc) > stored["expires"]:
        del otp_storage[email]
        return False
    
    if stored["otp"] == otp:
        del otp_storage[email]
        return True
    return False