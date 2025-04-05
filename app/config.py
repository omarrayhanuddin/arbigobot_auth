from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "138d0f9026618cdcffa8f23ad358e55baaf4afba26936d901297f92cb34ff8c4772b"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATABASE_URL: str = "postgresql+psycopg://postgres:root@localhost:5432/arb_test_db"
    
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SENDER_EMAIL: str = "example@gmail.com"
    SENDER_PASSWORD: str = "example"
    SITE_URL = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()