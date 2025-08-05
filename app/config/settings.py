from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AULA X Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/routes"
    
    # Base de datos
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "aula_x"
    
    # Seguridad
    SECRET_KEY: str = "aula_x_super_secret_key_franco_2024_desarrollo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    class Config:
        env_file = ".env"

settings = Settings()