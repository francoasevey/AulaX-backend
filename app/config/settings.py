# app/config/settings.py - TU CÓDIGO + Mejoras mínimas
from pydantic_settings import BaseSettings
from typing import List, Optional
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
    """Configuración de base de datos (Single Responsibility) - MEJORADA"""
    
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
        # 🆕 ÚNICA MEJORA: Manejar Atlas correctamente
        if "mongodb+srv://" in self._mongodb_url:
            # Atlas - ya incluye opciones en la URL
            return f"{self._mongodb_url}/{self._database_name}?retryWrites=true&w=majority"
        else:
            # Local/Docker - tu lógica original
            return f"{self._mongodb_url}/{self._database_name}"
    
    # 🆕 ÚNICO MÉTODO NUEVO: Detectar tipo de conexión
    def get_connection_type(self) -> str:
        """Determinar tipo de conexión para logging"""
        if "mongodb+srv://" in self._mongodb_url:
            return "MongoDB Atlas"
        elif "localhost" in self._mongodb_url or "127.0.0.1" in self._mongodb_url:
            return "MongoDB Local"
        else:
            return "MongoDB Remote"

class SecurityConfiguration:
    """Configuración de seguridad (Single Responsibility) - SIN CAMBIOS"""
    
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

# 🆕 NUEVA CLASE: Para IA (Single Responsibility)
class AIConfiguration:
    """Configuración de IA (Single Responsibility)"""
    
    def __init__(self, openai_api_key: str = ""):
        self._openai_api_key = openai_api_key
    
    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key
    
    def is_configured(self) -> bool:
        """Verificar si la IA está configurada"""
        return bool(self._openai_api_key and self._openai_api_key.strip())

class ApplicationSettings(BaseSettings, IConfigurationSettings):
    """Configuración principal de la aplicación (Composition over Inheritance) - TU CÓDIGO + Mejoras"""
    
    # Configuración básica - TU CÓDIGO ORIGINAL
    PROJECT_NAME: str = "AULA X Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"  # 🔧 Cambié a v1 para ser más estándar
    
    # Base de datos - TU CÓDIGO ORIGINAL
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "aula_x"
    
    # Seguridad - TU CÓDIGO ORIGINAL
    SECRET_KEY: str = "aula_x_super_secret_key_franco_2024_desarrollo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # CORS y hosts - TU CÓDIGO ORIGINAL
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Tecnologías específicas - TU CÓDIGO ORIGINAL
    OPENAI_API_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"
    
    # 🆕 NUEVOS CAMPOS OPCIONALES: Para AWS completo
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 🆕 ÚNICA ADICIÓN: Permitir campos extra sin error
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TU LÓGICA ORIGINAL
        self._database_config = DatabaseConfiguration(
            self.MONGODB_URL, 
            self.DATABASE_NAME
        )
        self._security_config = SecurityConfiguration(
            self.SECRET_KEY,
            self.ALGORITHM,
            self.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        # 🆕 ÚNICA ADICIÓN: Configuración IA
        self._ai_config = AIConfiguration(self.OPENAI_API_KEY)
    
    # TUS MÉTODOS ORIGINALES - SIN CAMBIOS
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
    
    # 🆕 ÚNICO MÉTODO NUEVO: Para IA
    def get_ai_config(self) -> AIConfiguration:
        """Obtener configuración de IA"""
        return self._ai_config
    
    def is_development(self) -> bool:
        """Verificar si está en modo desarrollo"""
        return self.ENVIRONMENT == "development"
    
    def is_production(self) -> bool:
        """Verificar si está en modo producción"""
        return self.ENVIRONMENT == "production"
    
    # 🆕 ÚNICO MÉTODO NUEVO: Para logging
    def get_connection_type(self) -> str:
        """Obtener tipo de conexión para logging"""
        return self._database_config.get_connection_type()

# Factory pattern para crear configuraciones - TU CÓDIGO ORIGINAL
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

# Singleton para configuraciones globales - TU CÓDIGO ORIGINAL
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

# Instancia global - TU CÓDIGO ORIGINAL
settings = GlobalSettings().get_settings()