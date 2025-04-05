from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from .schemas import User, UserCreate, Token, PasswordReset, OTPRequest, OTPVerify
from .crud import create_user, get_user_by_email
from .auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    generate_otp,
    store_otp,
    verify_otp,
)
from .dependencies import get_current_user, get_current_admin
from .database import get_db, init_db, engine
from .utils.email import send_verification_email
from .config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from datetime import timedelta
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="User Management API",
    description="API with user auth, admin features, otp login, and email verification",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/admin/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_user = await create_user(db, user)
        token = create_access_token(data={"sub": user.email})
        await send_verification_email(user.email, token)
        return db_user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")


@app.post("/auth/admin/token", response_model=Token)
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/admin/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")

        user = await get_user_by_email(db, email)
        if not user or user.is_verified:
            raise HTTPException(
                status_code=400, detail="Email already verified or invalid"
            )

        user.is_verified = True
        await db.commit()
        return {"message": "Email verified successfully"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid verification token")


@app.post("/auth/admin/login")
async def login(otp_request: OTPRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, otp_request.email)
    if not user or not verify_password(otp_request.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Generate and store OTP
    otp = generate_otp()
    store_otp(user.email, otp)

    # Send OTP via email
    await send_verification_email(
        user.email, f"Your OTP is: {otp} (valid for 5 minutes)"
    )

    return {"message": "OTP sent to your email"}


@app.post("/auth/admin/verify-otp", response_model=Token)
async def verify_otp_endpoint(
    otp_verify: OTPVerify, db: AsyncSession = Depends(get_db)
):
    if not verify_otp(otp_verify.email, otp_verify.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = await get_user_by_email(db, otp_verify.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/admin/password-reset-request")
async def password_reset_request(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = create_access_token(data={"sub": email})
    await send_verification_email(email, reset_token)
    return {"message": "Password reset link sent to email"}


@app.post("/auth/admin/password-reset")
async def password_reset(reset: PasswordReset, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            reset.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")

        user = await get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid reset request")

        user.password = get_password_hash(reset.new_password)
        await db.commit()
        return {"message": "Password reset successfully"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")


@app.get("/auth/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# @app.get("/auth/admin/admin/users", response_model=list[User])
# async def get_all_users(
#     db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)
# ):
#     result = await db.execute(select(User))
#     users = result.scalars().all()
#     return users


# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     return {"detail": exc.detail, "status_code": exc.status_code}

# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     return {"detail": "Internal server error", "status_code": 500}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
