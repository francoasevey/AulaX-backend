# ===== app/config/database.py - VERSIÓN CORREGIDA SIMPLE =====
"""
Servicio de base de datos con auto-configuración desde .env + switch manual
Mantiene funcionalidad original + gestión modular
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

from app.config.settings import settings, DatabaseConfiguration
from app.database.module_manager import ModuleManager

logger = logging.getLogger(__name__)

# ===== INTERFACES (SOLID - Interface Segregation Principle) =====
class IDatabaseConnection(ABC):
    """Interface para conexiones de base de datos"""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def get_database(self) -> AsyncIOMotorDatabase:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass

# ===== CONEXIÓN MONGODB (Igual que tu original) =====
class MongoDBConnection(IDatabaseConnection):
    """Implementación MongoDB con flexibilidad de conexión"""
    
    def __init__(self, database_config: DatabaseConfiguration):
        self._config = database_config
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Conectar a MongoDB con configuración optimizada"""
        try:
            connection_url = self._config.connection_url
            
            # Opciones de conexión optimizadas
            connection_options = {
                "maxPoolSize": 50,
                "minPoolSize": 5,
                "serverSelectionTimeoutMS": 5000,
                "socketTimeoutMS": 45000,
                "connectTimeoutMS": 10000,
            }
            
            # Si es Atlas, agregar opciones específicas
            if "mongodb+srv://" in connection_url:
                connection_options.update({
                    "retryWrites": True,
                    "w": "majority"
                })
            
            # Log del tipo de conexión
            connection_type = settings.get_connection_type()
            logger.info(f"🔗 Conectando a {connection_type}...")
            logger.info(f"🔗 Host: {getattr(self._config, 'host', 'N/A')}")
            logger.info(f"🔗 Puerto: {getattr(self._config, 'port', 'N/A')}")
            logger.info(f"🔗 Base de datos: {self._config.database_name}")
            
            # Crear cliente con opciones optimizadas
            self._client = AsyncIOMotorClient(
                connection_url,
                **connection_options
            )
            
            self._database = self._client[self._config.database_name]
            
            # Verificar conexión
            await self._client.admin.command('ping')
            self._is_connected = True
            
            logger.info(f"✅ Conectado exitosamente a {connection_type}")
            logger.info(f"✅ Base de datos: {self._config.database_name}")
            
            # Log adicional para Atlas
            if "mongodb+srv://" in connection_url:
                logger.info(f"🌍 Conexión Atlas establecida exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            logger.error(f"❌ Host: {getattr(self._config, 'host', 'N/A')}")
            logger.error(f"❌ Puerto: {getattr(self._config, 'port', 'N/A')}")
            self._is_connected = False
            raise ConnectionError(f"No se pudo conectar a MongoDB: {e}")
    
    async def disconnect(self) -> None:
        """Desconectar de MongoDB"""
        if self._client:
            self._client.close()
            self._is_connected = False
            connection_type = settings.get_connection_type()
            logger.info(f"❌ Desconectado de {connection_type}")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if not self._is_connected or self._database is None:
            raise RuntimeError("Base de datos no inicializada. Ejecutar connect() primero.")
        return self._database
    
    async def health_check(self) -> bool:
        """Verificar salud de la conexión"""
        try:
            if not self._client:
                return False
            
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._is_connected

# ===== FACTORY PATTERN SIMPLE =====
class DatabaseFactory:
    """Factory para crear instancias de base de datos"""
    
    @staticmethod
    def create_mongodb_connection(config: Optional[DatabaseConfiguration] = None) -> IDatabaseConnection:
        """Crear conexión MongoDB con configuración"""
        if config is None:
            config = settings.get_database_config()
        return MongoDBConnection(config)

# ===== SERVICIO PRINCIPAL HÍBRIDO =====
class OptimizedDatabaseService:
    """
    Servicio de base de datos optimizado con:
    1. Auto-configuración desde .env al inicializar
    2. Switch manual cuando se necesite
    3. Gestión modular
    """
    
    def __init__(self):
        self._connection: Optional[IDatabaseConnection] = None
        self._module_manager: Optional[ModuleManager] = None
        
        # 🎯 CONFIGURACIÓN SIMPLE DE MÓDULOS
        self._active_modules = [
            "auth",      # ← Siempre activo (requerido)
            #"academic"   # ← Agrega más aquí cuando los necesites
            # "tasks",
            # "content", 
            # "communication",
            # "gamification",
            # "analytics"
        ]
    
    async def initialize(self) -> None:
        """
        Inicializar servicio con auto-configuración desde .env
        Template Method Pattern
        """
        logger.info("🚀 Inicializando servicio de base de datos optimizado...")
        
        # 1. Auto-configurar desde .env
        await self._auto_configure_from_env()
        
        # 2. Inicializar gestor de módulos
        self._module_manager = ModuleManager(
            database=self._connection.get_database(),
            active_modules=self._active_modules
        )
        
        # 3. Configurar módulos activos
        await self._module_manager.setup_modules()
        
        # 4. Datos iniciales
        await self._create_initial_data()
        
        logger.info("🎉 Servicio optimizado inicializado correctamente")
        logger.info(f"📦 Módulos activos: {', '.join(self._active_modules)}")
    
    async def _auto_configure_from_env(self) -> None:
        """
        🆕 AUTO-CONFIGURACIÓN DESDE .env
        FUNCIONA CON TU .env ACTUAL usando MONGODB_URL
        """
        try:
            # Usar tu MONGODB_URL directamente
            mongodb_url = getattr(settings, 'MONGODB_URL', '')
            database_name = getattr(settings, 'DATABASE_NAME', 'aula_x')
            
            if not mongodb_url:
                logger.error("❌ MONGODB_URL no encontrada en .env")
                raise ConnectionError("MONGODB_URL requerida en .env")
            
            # Detectar tipo de conexión automáticamente desde la URL
            connection_type = self._detect_connection_type_from_url(mongodb_url)
            logger.info(f"🔧 Auto-configurando desde .env: {connection_type}")
            
            # Crear configuración usando tu MONGODB_URL
            config = DatabaseConfiguration(mongodb_url, database_name)
            
            # Conectar
            self._connection = DatabaseFactory.create_mongodb_connection(config)
            await self._connection.connect()
            
            logger.info(f"✅ Auto-configuración exitosa usando: {connection_type}")
            
        except Exception as e:
            logger.error(f"❌ Error en auto-configuración: {e}")
            raise e
    
    def _detect_connection_type_from_url(self, mongodb_url: str) -> str:
        """Detectar tipo de conexión desde la URL"""
        if "mongodb+srv://" in mongodb_url:
            return "MongoDB Atlas"
        elif "@" in mongodb_url and "localhost" not in mongodb_url:
            return "MongoDB Docker/Remote"
        else:
            return "MongoDB Local"
    
    # ===== MÉTODOS PARA CAMBIAR URL COMPLETA (NUEVO) =====
    async def switch_to_url(self, mongodb_url: str, database_name: str = "aula_x") -> bool:
        """
        🆕 Cambiar usando URL completa (como tu .env)
        Útil para cambiar rápidamente entre las URLs comentadas en tu .env
        """
        try:
            connection_type = self._detect_connection_type_from_url(mongodb_url)
            logger.info(f"🔄 Switch usando URL completa a: {connection_type}")
            
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Crear nueva configuración
            new_config = DatabaseConfiguration(mongodb_url, database_name)
            
            # Crear nueva conexión
            self._connection = DatabaseFactory.create_mongodb_connection(new_config)
            await self._connection.connect()
            
            # Reconfigurar módulos después del switch
            if self._module_manager:
                await self._reconfigure_modules_after_switch()
            
            logger.info(f"✅ Switch completado a: {connection_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en switch con URL: {e}")
            return False
    
    # ===== MÉTODOS DE SWITCH SIMPLIFICADOS PARA TU .env =====
    #async def switch_to_atlas_env(self) -> bool:
        """Cambiar a Atlas usando la URL de tu .env"""
        atlas_url = "mongodb+srv://francoasevey:2kDokCGxhxXoFqRl@francocluster.cw9qc37.mongodb.net/aula_x"
        return await self.switch_to_url(atlas_url)
    
    #async def switch_to_local_env(self) -> bool:
        """Cambiar a Local usando la URL de tu .env"""
        local_url = "mongodb://localhost:27017/aula_x"
        return await self.switch_to_url(local_url)
    
    #async def switch_to_docker_env(self) -> bool:
        """Cambiar a Docker usando la URL de tu .env"""
        docker_url = "mongodb://admin:admin123@localhost:27017/aula_x"
        return await self.switch_to_url(docker_url)
    
    async def _create_initial_data(self) -> None:
        """Crear datos iniciales solo si es necesario"""
        try:
            db = self.get_database()
            
            # Verificar admin
            admin_count = await db.users.count_documents({"role": "administrator"})
            
            if admin_count == 0:
                logger.info("👤 Creando usuario administrador inicial...")
                
                admin_user = {
                    "email": "admin@aulax.com",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPu8VDjL8QOrS",
                    "role": "administrator",
                    "status": "active",
                    "profile": {
                        "first_name": "Administrador",
                        "last_name": "Sistema",
                        "bio": "Usuario administrador del sistema AULA X"
                    },
                    "email_verified": True,
                    "is_active": True
                }
                
                await db.users.insert_one(admin_user)
                logger.info("✅ Admin creado: admin@aulax.com / admin123")
        
        except Exception as e:
            logger.error(f"❌ Error creando datos iniciales: {e}")
    
    # ===== MÉTODOS DE SWITCH MANUAL (TU FUNCIONALIDAD ORIGINAL) =====
    async def switch_to_atlas(self, cluster_url: str, username: str, password: str, database: str = "aula_x") -> bool:
        """Cambiar a conexión Atlas manualmente"""
        try:
            logger.info(f"🔄 Switch manual a Atlas: {cluster_url}")
            
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb+srv://{username}:{password}@{cluster_url}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = DatabaseFactory.create_mongodb_connection(new_config)
            await self._connection.connect()
            
            # 🆕 RECONFIGURAR MÓDULOS después del switch
            if self._module_manager:
                await self._reconfigure_modules_after_switch()
            
            logger.info("✅ Switch a Atlas completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a Atlas: {e}")
            return False
    
    async def switch_to_local(self, host: str = "localhost", port: int = 27017, database: str = "aula_x") -> bool:
        """Cambiar a conexión local manualmente"""
        try:
            logger.info(f"🔄 Switch manual a Local: {host}:{port}")
            
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb://{host}:{port}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = DatabaseFactory.create_mongodb_connection(new_config)
            await self._connection.connect()
            
            # 🆕 RECONFIGURAR MÓDULOS después del switch
            if self._module_manager:
                await self._reconfigure_modules_after_switch()
            
            logger.info("✅ Switch a Local completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a local: {e}")
            return False
    
    async def switch_to_docker(self, host: str = "localhost", port: int = 27017, 
                             username: str = "admin", password: str = "admin123", 
                             database: str = "aula_x") -> bool:
        """Cambiar a conexión Docker manualmente"""
        try:
            logger.info(f"🔄 Switch manual a Docker: {host}:{port}")
            
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb://{username}:{password}@{host}:{port}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = DatabaseFactory.create_mongodb_connection(new_config)
            await self._connection.connect()
            
            # 🆕 RECONFIGURAR MÓDULOS después del switch
            if self._module_manager:
                await self._reconfigure_modules_after_switch()
            
            logger.info("✅ Switch a Docker completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a Docker: {e}")
            return False
    
    async def _reconfigure_modules_after_switch(self) -> None:
        """🆕 Reconfigurar módulos después de switch de conexión"""
        try:
            logger.info("🔄 Reconfigurando módulos después del switch...")
            
            # Actualizar referencia de base de datos en ModuleManager
            new_database = self._connection.get_database()
            await self._module_manager.reconfigure_database(new_database)
            
            # Reinicializar módulos activos
            await self._module_manager.reinitialize_modules()
            
            logger.info("✅ Módulos reconfigurados después del switch")
            
        except Exception as e:
            logger.error(f"❌ Error reconfigurando módulos: {e}")
            # No hacer raise aquí para no fallar el switch completo
    
    # ===== MÉTODOS DE GESTIÓN MODULAR =====
    async def add_module(self, module_name: str) -> bool:
        """Agregar módulo dinámicamente"""
        try:
            if module_name not in self._active_modules:
                self._active_modules.append(module_name)
                
                if self._module_manager:
                    await self._module_manager.add_module(module_name)
                
                logger.info(f"✅ Módulo '{module_name}' agregado exitosamente")
                return True
            else:
                logger.warning(f"⚠️ Módulo '{module_name}' ya está activo")
                return False
        except Exception as e:
            logger.error(f"❌ Error agregando módulo '{module_name}': {e}")
            return False
    
    async def remove_module(self, module_name: str) -> bool:
        """Remover módulo (conserva datos)"""
        try:
            if module_name == "auth":
                logger.error("❌ No se puede remover el módulo 'auth' (requerido)")
                return False
            
            if module_name in self._active_modules:
                self._active_modules.remove(module_name)
                
                if self._module_manager:
                    await self._module_manager.remove_module(module_name)
                
                logger.info(f"✅ Módulo '{module_name}' removido")
                return True
            else:
                logger.warning(f"⚠️ Módulo '{module_name}' no está activo")
                return False
        except Exception as e:
            logger.error(f"❌ Error removiendo módulo '{module_name}': {e}")
            return False
    
    def get_active_modules(self) -> List[str]:
        """Obtener módulos activos"""
        return self._active_modules.copy()
    
    async def get_module_status(self) -> Dict[str, Any]:
        """Obtener estado detallado de módulos"""
        if not self._module_manager:
            return {"error": "Module manager no inicializado"}
        
        return await self._module_manager.get_status()
    
    # ===== MÉTODOS DE SERVICIO =====
    async def shutdown(self) -> None:
        """Shutdown graceful del servicio"""
        logger.info("🔄 Iniciando shutdown del servicio...")
        
        try:
            if self._module_manager:
                # Cleanup de módulos
                for module_name in self._active_modules.copy():
                    if module_name != "auth":  # Mantener auth hasta el final
                        await self.remove_module(module_name)
            
            if self._connection:
                await self._connection.disconnect()
            
            logger.info("✅ Shutdown completado")
            
        except Exception as e:
            logger.error(f"❌ Error en shutdown: {e}")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if not self._connection:
            raise RuntimeError("Servicio de base de datos no inicializado")
        return self._connection.get_database()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check completo con información detallada"""
        base_status = {
            "healthy": False,
            "active_modules": self._active_modules,
        }
        
        if not self._connection:
            base_status.update({
                "status": "disconnected",
                "error": "No connection available"
            })
            return base_status
        
        try:
            is_healthy = await self._connection.health_check()
            base_status["healthy"] = is_healthy
            
            if is_healthy:
                db = self.get_database()
                db_stats = await db.command("dbStats")
                collection_names = await db.list_collection_names()
                
                base_status.update({
                    "status": "connected",
                    "connection_type": settings.get_connection_type(),
                    "database": settings.get_database_config().database_name,
                    "stats": {
                        "collections": len(collection_names),
                        "collection_names": collection_names,
                        "data_size": db_stats.get("dataSize", 0),
                        "storage_size": db_stats.get("storageSize", 0),
                        "indexes": db_stats.get("indexes", 0)
                    }
                })
                
                # Agregar estado de módulos si está disponible
                if self._module_manager:
                    module_status = await self._module_manager.get_status()
                    base_status["module_status"] = module_status
            else:
                base_status.update({
                    "status": "error",
                    "error": "Health check failed"
                })
        
        except Exception as e:
            logger.warning(f"⚠️ Error en health check: {e}")
            base_status.update({
                "status": "error", 
                "error": str(e),
                "healthy": False
            })
        
        return base_status
    
    # ===== MÉTODO PARA RECARGAR CONFIGURACIÓN =====
    async def reload_from_env(self) -> bool:
        """
        🆕 Recargar configuración desde .env sin reiniciar la aplicación
        FUNCIONA CON TU .env ACTUAL
        """
        try:
            logger.info("🔄 Recargando configuración desde .env...")
            
            # Reimportar settings para obtener nuevos valores
            import importlib
            from app.config import settings as settings_module
            importlib.reload(settings_module)
            
            # Reconectar usando MONGODB_URL actualizada
            await self._auto_configure_from_env()
            
            # Reconfigurar módulos
            if self._module_manager:
                await self._reconfigure_modules_after_switch()
            
            logger.info("✅ Configuración recargada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recargando configuración: {e}")
            return False

# ===== EJEMPLO DE USO ACTUALIZADO =====
"""
🚀 FUNCIONA PERFECTO CON TU .env:

1. INICIALIZACIÓN AUTOMÁTICA:
   await database_service.initialize()  # Usa tu MONGODB_URL automáticamente

2. CAMBIAR SOLO EDITANDO .env:
   - Cambia la línea MONGODB_URL en tu .env
   - Descomenta la URL que quieres usar
   - Llama: await database_service.reload_from_env()

3. SWITCH PROGRAMÁTICO RÁPIDO:
   await database_service.switch_to_atlas_env()   # Usa tu URL de Atlas
   await database_service.switch_to_local_env()   # Usa tu URL Local
   await database_service.switch_to_docker_env()  # Usa tu URL Docker
   
4. SWITCH CON URL PERSONALIZADA:
   await database_service.switch_to_url("mongodb://custom:url@host:port/db")

5. TU FUNCIONALIDAD ORIGINAL SIGUE FUNCIONANDO:
   await database_service.switch_to_atlas("cluster", "user", "pass")
   await database_service.switch_to_local("localhost", 27017)
   await database_service.switch_to_docker("localhost", 27017, "admin", "admin123")

✅ FLUJO SIMPLE QUE QUERÍAS:
1. Cambias MONGODB_URL en .env (descomenta la línea que quieres)
2. Opción A: Reinicias aplicación (auto-configuración)
3. Opción B: Llamas reload_from_env() (sin reiniciar)
4. ¡Listo! Conectado a la nueva base de datos
"""

# ===== SINGLETON PATTERN =====
class GlobalDatabaseService:
    """Singleton para servicio global de base de datos"""
    
    _instance = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_service(self) -> OptimizedDatabaseService:
        """Obtener servicio de base de datos"""
        if self._service is None:
            self._service = OptimizedDatabaseService()
        return self._service
    
    def reset_service(self) -> OptimizedDatabaseService:
        """Resetear servicio (útil para testing)"""
        self._service = OptimizedDatabaseService()
        return self._service

# ===== INSTANCIAS GLOBALES =====
# Singleton instance
database_service = GlobalDatabaseService().get_service()

# Función de conveniencia para Dependency Injection
async def get_database() -> AsyncIOMotorDatabase:
    """Función helper para obtener base de datos (Dependency Injection)"""
    return database_service.get_database()

# Función para obtener servicio completo
def get_database_service() -> OptimizedDatabaseService:
    """Obtener servicio completo para operaciones avanzadas"""
    return database_service

# ===== EJEMPLO DE USO =====
"""
🚀 INICIALIZACIÓN AUTOMÁTICA DESDE .env:
await database_service.initialize()  # Lee DB_TYPE del .env y conecta automáticamente

🔄 SWITCH MANUAL (tu funcionalidad original):
await database_service.switch_to_atlas("cluster0.abc123.mongodb.net", "user", "pass")
await database_service.switch_to_local("localhost", 27017)
await database_service.switch_to_docker("localhost", 27017, "admin", "admin123")

🆕 RECARGAR DESDE .env SIN REINICIAR:
await database_service.reload_from_env()  # Útil para cambios en producción

📦 GESTIÓN DE MÓDULOS:
await database_service.add_module("tasks")
await database_service.remove_module("content")
modules = database_service.get_active_modules()

📊 MONITOREO:
health = await database_service.health_check()
module_status = await database_service.get_module_status()
"""