from pydantic_settings import BaseSettings
from typing import List
from abc import ABC, abstractmethod

class IConfigurationSettings(ABC):
    """Interface para configuraciones (Dependency Inversion Principle)"""
    
    @property
    @abstractmethod
    def database_url(self) -> str:
        pass
    
    @property
    @abstractmethod
    def allowed_hosts(self) -> List[str]:
        pass

class DatabaseConfiguration:
    """Configuración de base de datos (Single Responsibility)"""
    
    def __init__(self, mongodb_url: str, database_name: str):
        self._mongodb_url = mongodb_url
        self._database_name = database_name
    
    @property
    def connection_url(self) -> str:
        return self._mongodb_url
    
    @property
    def database_name(self) -> str:
        return self._database_name
    
    def get_full_connection_string(self) -> str:
        """Obtener string de conexión completo"""
        return f"{self._mongodb_url}/{self._database_name}"

class SecurityConfiguration:
    """Configuración de seguridad (Single Responsibility)"""
    
    def __init__(self, secret_key: str, algorithm: str, token_expire_minutes: int):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._token_expire_minutes = token_expire_minutes
    
    @property
    def secret_key(self) -> str:
        return self._secret_key
    
    @property
    def algorithm(self) -> str:
        return self._algorithm
    
    @property
    def token_expire_minutes(self) -> int:
        return self._token_expire_minutes
    
    def is_secure_key(self) -> bool:
        """Validar si la clave es segura"""
        return len(self._secret_key) >= 32

class ApplicationSettings(BaseSettings, IConfigurationSettings):
    """Configuración principal de la aplicación (Composition over Inheritance)"""
    
    # Configuración básica
    PROJECT_NAME: str = "AULA X Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/routes"
    
    # Base de datos
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "aula_x"
    
    # Seguridad
    SECRET_KEY: str = "aula_x_super_secret_key_franco_2024_desarrollo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # CORS y hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Tecnologías específicas del PDF
    OPENAI_API_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._database_config = DatabaseConfiguration(
            self.MONGODB_URL, 
            self.DATABASE_NAME
        )
        self._security_config = SecurityConfiguration(
            self.SECRET_KEY,
            self.ALGORITHM,
            self.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    @property
    def database_url(self) -> str:
        """Implementación de interface (Interface Segregation)"""
        return self._database_config.connection_url
    
    @property
    def allowed_hosts(self) -> List[str]:
        """Implementación de interface (Interface Segregation)"""
        return self.ALLOWED_HOSTS
    
    def get_database_config(self) -> DatabaseConfiguration:
        """Obtener configuración de base de datos"""
        return self._database_config
    
    def get_security_config(self) -> SecurityConfiguration:
        """Obtener configuración de seguridad"""
        return self._security_config
    
    def is_development(self) -> bool:
        """Verificar si está en modo desarrollo"""
        return self.ENVIRONMENT == "development"
    
    def is_production(self) -> bool:
        """Verificar si está en modo producción"""
        return self.ENVIRONMENT == "production"

# Factory pattern para crear configuraciones
class SettingsFactory:
    """Factory para crear configuraciones (Factory Pattern)"""
    
    @staticmethod
    def create_settings() -> ApplicationSettings:
        """Crear instancia de configuraciones"""
        return ApplicationSettings()
    
    @staticmethod
    def create_test_settings() -> ApplicationSettings:
        """Crear configuraciones para testing"""
        settings = ApplicationSettings()
        settings.DATABASE_NAME = f"{settings.DATABASE_NAME}_test"
        settings.DEBUG = True
        return settings

# Singleton para configuraciones globales
class GlobalSettings:
    """Singleton para configuraciones globales (Singleton Pattern)"""
    
    _instance = None
    _settings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_settings(self) -> ApplicationSettings:
        """Obtener configuraciones (Lazy Loading)"""
        if self._settings is None:
            self._settings = SettingsFactory.create_settings()
        return self._settings

# Instancia global
settings = GlobalSettings().get_settings()