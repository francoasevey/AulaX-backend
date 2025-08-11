# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
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
            # Inicializar base de datos
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
    """Servicio de health checks mejorado (Single Responsibility)"""
    
    @staticmethod
    async def get_application_health() -> Dict[str, Any]:
        """Obtener estado de salud de la aplicación"""
        database_health = await database_service.health_check()
        ai_config = settings.get_ai_config()
        
        return {
            "status": "healthy" if database_health["healthy"] else "unhealthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "connection_type": settings.get_connection_type(),
            "services": {
                "database": database_health,
                "ai": {
                    "configured": ai_config.is_configured(),
                    "model": ai_config.model if ai_config.is_configured() else None
                }
            },
            "features": {
                "academic_planning": True,
                "ai_evaluation": ai_config.is_configured(),
                "content_management": True,
                "real_time_chat": True,
                "notifications": True,
                "parent_portal": True
            }
        }

class DatabaseManagementService:
    """Servicio para gestión dinámica de conexiones de BD"""
    
    @staticmethod
    async def switch_connection_type(connection_type: str, **kwargs) -> Dict[str, Any]:
        """Cambiar tipo de conexión dinámicamente"""
        try:
            if connection_type == "atlas":
                required_fields = ["cluster_url", "username", "password"]
                if not all(field in kwargs for field in required_fields):
                    raise ValueError(f"Atlas requiere: {required_fields}")
                
                success = await database_service.switch_to_atlas(
                    kwargs["cluster_url"],
                    kwargs["username"],
                    kwargs["password"],
                    kwargs.get("database", "aula_x")
                )
                
            elif connection_type == "local":
                success = await database_service.switch_to_local(
                    kwargs.get("host", "localhost"),
                    kwargs.get("port", 27017),
                    kwargs.get("database", "aula_x")
                )
                
            elif connection_type == "docker":
                success = await database_service.switch_to_docker(
                    kwargs.get("host", "localhost"),
                    kwargs.get("port", 27017),
                    kwargs.get("username", "admin"),
                    kwargs.get("password", "admin123"),
                    kwargs.get("database", "aula_x")
                )
            else:
                raise ValueError(f"Tipo de conexión no soportado: {connection_type}")
            
            if success:
                health = await database_service.health_check()
                return {
                    "success": True,
                    "message": f"Conexión cambiada exitosamente a {connection_type}",
                    "new_connection": health
                }
            else:
                return {
                    "success": False,
                    "message": f"Error cambiando conexión a {connection_type}"
                }
                
        except Exception as e:
            logger.error(f"Error en cambio de conexión: {e}")
            return {
                "success": False,
                "message": str(e)
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
                "connection_type": settings.get_connection_type(),
                "docs": "/docs" if settings.is_development() else "Documentación deshabilitada en producción",
                "features": [
                    "🎯 Planificación Académica con IA",
                    "📝 Evaluación Automática de Tareas", 
                    "📚 Gestión Inteligente de Contenidos",
                    "💬 Comunicación y Chat en Tiempo Real",
                    "🤖 AulaBot - Asistente Inteligente",
                    "👨‍👩‍👧‍👦 Portal para Padres/Tutores",
                    "📊 Dashboard Predictivo",
                    "🎮 Gamificación Educativa"
                ],
                "api_endpoints": {
                    "health": "/health",
                    "info": "/info",
                    "database": "/database/*",
                    "api_v1": settings.API_V1_STR
                }
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
                    "connection_type": settings.get_connection_type(),
                    "name": settings.get_database_config().database_name,
                    "host": settings.MONGO_HOST
                },
                "security": {
                    "algorithm": settings.get_security_config().algorithm,
                    "token_expire_minutes": settings.get_security_config().token_expire_minutes
                },
                "ai": {
                    "configured": settings.get_ai_config().is_configured(),
                    "model": settings.get_ai_config().model
                },
                "technologies": [
                    "FastAPI", "MongoDB", "Motor", "Pydantic", 
                    "OpenAI", "AWS S3", "JWT", "BCrypt", "Vue.js", "TailwindCSS"
                ],
                "modules": [
                    "Authentication & Authorization",
                    "Academic Planning",
                    "Task Management & AI Evaluation", 
                    "Content Management",
                    "Real-time Communication",
                    "Intelligent Notifications",
                    "Parent Portal",
                    "Analytics Dashboard"
                ]
            }
        
        # === ENDPOINTS DE GESTIÓN DE BASE DE DATOS ===
        
        @app.get("/database/status")
        async def database_status() -> Dict[str, Any]:
            """Estado detallado de la base de datos"""
            try:
                return await database_service.health_check()
            except Exception as e:
                logger.error(f"Error obteniendo estado de BD: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/database/switch-to-atlas")
        async def switch_to_atlas_endpoint(
            cluster_url: str,
            username: str,
            password: str,
            database: str = "aula_x"
        ) -> Dict[str, Any]:
            """Cambiar conexión a MongoDB Atlas"""
            try:
                return await DatabaseManagementService.switch_connection_type(
                    "atlas",
                    cluster_url=cluster_url,
                    username=username,
                    password=password,
                    database=database
                )
            except Exception as e:
                logger.error(f"Error cambiando a Atlas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/database/switch-to-local")
        async def switch_to_local_endpoint(
            host: str = "localhost",
            port: int = 27017,
            database: str = "aula_x"
        ) -> Dict[str, Any]:
            """Cambiar conexión a MongoDB local"""
            try:
                return await DatabaseManagementService.switch_connection_type(
                    "local",
                    host=host,
                    port=port,
                    database=database
                )
            except Exception as e:
                logger.error(f"Error cambiando a local: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/database/switch-to-docker")
        async def switch_to_docker_endpoint(
            host: str = "localhost",
            port: int = 27017,
            username: str = "admin", 
            password: str = "admin123",
            database: str = "aula_x"
        ) -> Dict[str, Any]:
            """Cambiar conexión a MongoDB en Docker"""
            try:
                return await DatabaseManagementService.switch_connection_type(
                    "docker",
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database
                )
            except Exception as e:
                logger.error(f"Error cambiando a Docker: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/database/collections")
        async def list_collections() -> Dict[str, Any]:
            """Listar colecciones de la base de datos"""
            try:
                db = database_service.get_database()
                collections = await db.list_collection_names()
                
                # Obtener estadísticas de cada colección
                collection_stats = {}
                for collection_name in collections:
                    try:
                        stats = await db.command("collStats", collection_name)
                        collection_stats[collection_name] = {
                            "count": stats.get("count", 0),
                            "size": stats.get("size", 0),
                            "avg_obj_size": stats.get("avgObjSize", 0)
                        }
                    except:
                        collection_stats[collection_name] = {"count": 0, "size": 0}
                
                return {
                    "database": settings.get_database_config().database_name,
                    "total_collections": len(collections),
                    "collections": collections,
                    "stats": collection_stats
                }
            except Exception as e:
                logger.error(f"Error listando colecciones: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === ENDPOINTS DE CONFIGURACIÓN ===
        
        @app.get("/config/current")
        async def get_current_config() -> Dict[str, Any]:
            """Obtener configuración actual"""
            return {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "database": {
                    "type": settings.get_connection_type(),
                    "host": settings.MONGO_HOST,
                    "port": settings.MONGO_PORT,
                    "database": settings.MONGO_DATABASE,
                    "has_auth": bool(settings.MONGO_USERNAME)
                },
                "ai": {
                    "configured": settings.get_ai_config().is_configured(),
                    "model": settings.get_ai_config().model
                },
                "security": {
                    "algorithm": settings.get_security_config().algorithm,
                    "token_expire_minutes": settings.get_security_config().token_expire_minutes,
                    "secure_key": settings.get_security_config().is_secure_key()
                }
            }
        
        @app.get("/config/connection-examples")
        async def get_connection_examples() -> Dict[str, Any]:
            """Ejemplos de configuración para diferentes tipos de conexión"""
            return {
                "atlas": {
                    "description": "MongoDB Atlas (Cloud)",
                    "env_variables": {
                        "MONGO_HOST": "cluster0.xxxxx.mongodb.net",
                        "MONGO_USERNAME": "tu_usuario",
                        "MONGO_PASSWORD": "tu_password",
                        "MONGO_DATABASE": "aula_x"
                    },
                    "example_call": "POST /database/switch-to-atlas"
                },
                "local": {
                    "description": "MongoDB Local (sin autenticación)",
                    "env_variables": {
                        "MONGO_HOST": "localhost",
                        "MONGO_PORT": "27017",
                        "MONGO_DATABASE": "aula_x"
                    },
                    "example_call": "POST /database/switch-to-local"
                },
                "docker": {
                    "description": "MongoDB en Docker",
                    "env_variables": {
                        "MONGO_HOST": "localhost",
                        "MONGO_PORT": "27017",
                        "MONGO_USERNAME": "admin",
                        "MONGO_PASSWORD": "admin123",
                        "MONGO_DATABASE": "aula_x"
                    },
                    "example_call": "POST /database/switch-to-docker"
                }
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