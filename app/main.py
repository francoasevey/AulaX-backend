from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from app.config.settings import settings
from app.config.database import database_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MiddlewareManager:
    """Gestor de middlewares (Single Responsibility)"""
    
    @staticmethod
    def configure_cors(app: FastAPI) -> None:
        """Configurar CORS middleware"""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_hosts,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    @staticmethod
    def configure_security(app: FastAPI) -> None:
        """Configurar middlewares de seguridad"""
        if settings.is_production():
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=settings.allowed_hosts
            )

class ApplicationLifecycle:
    """Gestor del ciclo de vida de la aplicación (Single Responsibility)"""
    
    @staticmethod
    async def startup() -> None:
        """Inicializar servicios al arrancar"""
        try:
            await database_service.initialize()
            logger.info("🚀 Servicios inicializados correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}")
            raise e
    
    @staticmethod
    async def shutdown() -> None:
        """Cerrar servicios al apagar"""
        try:
            await database_service.shutdown()
            logger.info("🛑 Servicios cerrados correctamente")
        except Exception as e:
            logger.error(f"❌ Error cerrando servicios: {e}")

class HealthCheckService:
    """Servicio de health checks (Single Responsibility)"""
    
    @staticmethod
    async def get_application_health() -> Dict[str, Any]:
        """Obtener estado de salud de la aplicación"""
        database_health = await database_service.health_check()
        
        return {
            "status": "healthy" if database_health["healthy"] else "unhealthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": database_health
            }
        }

class FastAPIFactory:
    """Factory para crear aplicación FastAPI (Factory Pattern)"""
    
    @staticmethod
    def create_app() -> FastAPI:
        """Crear y configurar aplicación FastAPI"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await ApplicationLifecycle.startup()
            yield
            # Shutdown
            await ApplicationLifecycle.shutdown()
        
        # Crear aplicación
        application = FastAPI(
            title=settings.PROJECT_NAME,
            description="Sistema de Aula Virtual Inteligente con IA, Planificación, Evaluación y Comunicación",
            version=settings.VERSION,
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
            docs_url="/docs" if settings.is_development() else None,
            redoc_url="/redoc" if settings.is_development() else None,
            lifespan=lifespan
        )
        
        # Configurar middlewares
        MiddlewareManager.configure_cors(application)
        MiddlewareManager.configure_security(application)
        
        # Registrar endpoints
        FastAPIFactory._register_routes(application)
        
        return application
    
    @staticmethod
    def _register_routes(app: FastAPI) -> None:
        """Registrar rutas de la aplicación"""
        
        @app.get("/")
        async def root() -> Dict[str, Any]:
            """Endpoint raíz de la aplicación"""
            return {
                "message": "Bienvenido a AULA X - Sistema de Aula Virtual Inteligente",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "docs": "/docs" if settings.is_development() else "Documentación deshabilitada en producción",
                "features": [
                    "Planificación Académica",
                    "Evaluación con IA", 
                    "Gestión de Contenidos",
                    "Comunicación y Chat",
                    "Bot Inteligente"
                ]
            }
        
        @app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Endpoint de health check detallado"""
            try:
                health_status = await HealthCheckService.get_application_health()
                return health_status
            except Exception as e:
                logger.error(f"Error en health check: {e}")
                raise HTTPException(status_code=503, detail="Servicio no disponible")
        
        @app.get("/info")
        async def application_info() -> Dict[str, Any]:
            """Información detallada de la aplicación"""
            return {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "database": {
                    "type": "MongoDB",
                    "name": settings.get_database_config().database_name
                },
                "security": {
                    "algorithm": settings.get_security_config().algorithm,
                    "token_expire_minutes": settings.get_security_config().token_expire_minutes
                },
                "technologies": [
                    "FastAPI", "MongoDB", "Motor", "Pydantic", 
                    "OpenAI", "AWS S3", "JWT", "BCrypt"
                ]
            }

# Crear aplicación usando Factory Pattern
app = FastAPIFactory.create_app()

# Punto de entrada para uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development()
    )