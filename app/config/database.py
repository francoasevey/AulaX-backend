from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from app.config.settings import settings, DatabaseConfiguration

# Configurar logging
logger = logging.getLogger(__name__)

class IDatabaseConnection(ABC):
    """Interface para conexiones de base de datos (Interface Segregation)"""
    
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

class IDatabaseManager(ABC):
    """Interface para gestión de base de datos (Dependency Inversion)"""
    
    @abstractmethod
    async def initialize_indexes(self) -> None:
        pass
    
    @abstractmethod
    async def create_collections(self) -> None:
        pass

class MongoDBConnection(IDatabaseConnection):
    """Implementación específica para MongoDB (Open/Closed Principle)"""
    
    def __init__(self, database_config: DatabaseConfiguration):
        self._config = database_config
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Conectar a MongoDB con manejo de errores"""
        try:
            self._client = AsyncIOMotorClient(
                self._config.connection_url,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000
            )
            
            self._database = self._client[self._config.database_name]
            
            # Verificar conexión
            await self._client.admin.command('ping')
            self._is_connected = True
            
            logger.info(f"✅ Conectado exitosamente a MongoDB: {self._config.database_name}")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            self._is_connected = False
            raise ConnectionError(f"No se pudo conectar a MongoDB: {e}")
    
    async def disconnect(self) -> None:
        """Desconectar de MongoDB"""
        if self._client:
            self._client.close()
            self._is_connected = False
            logger.info("❌ Desconectado de MongoDB")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if not self._is_connected or not self._database:
            raise RuntimeError("Base de datos no inicializada. Ejecutar connect() primero.")
        return self._database
    
    async def health_check(self) -> bool:
        """Verificar salud de la conexión"""
        try:
            if not self._client:
                return False
            
            await self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._is_connected

class MongoDBIndexManager(IDatabaseManager):
    """Gestor de índices y colecciones de MongoDB (Single Responsibility)"""
    
    def __init__(self, connection: IDatabaseConnection):
        self._connection = connection
    
    async def initialize_indexes(self) -> None:
        """Crear índices necesarios para la aplicación"""
        try:
            db = self._connection.get_database()
            
            # Índices para usuarios
            await db.users.create_index("email", unique=True)
            await db.users.create_index("username", unique=True)
            await db.users.create_index([("role", 1), ("is_active", 1)])
            
            # Índices para contenidos académicos
            await db.academic_plans.create_index([("teacher_id", 1), ("subject", 1)])
            await db.academic_plans.create_index("date")
            
            # Índices para tareas
            await db.tasks.create_index([("teacher_id", 1), ("subject", 1)])
            await db.tasks.create_index([("student_id", 1), ("due_date", 1)])
            await db.tasks.create_index("created_at")
            
            # Índices para notificaciones
            await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
            await db.notifications.create_index("created_at")
            
            logger.info("✅ Índices creados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
            raise e
    
    async def create_collections(self) -> None:
        """Crear colecciones con validación de schema"""
        try:
            db = self._connection.get_database()
            
            # Definir schemas de validación
            user_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "username", "password_hash", "role"],
                    "properties": {
                        "email": {"bsonType": "string"},
                        "username": {"bsonType": "string"},
                        "role": {"enum": ["administrator", "teacher", "student", "parent"]}
                    }
                }
            }
            
            # Crear colecciones con validación
            collections_config = {
                "users": user_schema,
                "academic_plans": {},
                "tasks": {},
                "notifications": {},
                "chat_messages": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in await db.list_collection_names():
                    if schema:
                        await db.create_collection(collection_name, validator=schema)
                    else:
                        await db.create_collection(collection_name)
                    
                    logger.info(f"✅ Colección '{collection_name}' creada")
            
        except Exception as e:
            logger.error(f"❌ Error creando colecciones: {e}")
            raise e

class DatabaseFactory:
    """Factory para crear instancias de base de datos (Factory Pattern)"""
    
    @staticmethod
    def create_mongodb_connection() -> IDatabaseConnection:
        """Crear conexión MongoDB"""
        db_config = settings.get_database_config()
        return MongoDBConnection(db_config)
    
    @staticmethod
    def create_database_manager(connection: IDatabaseConnection) -> IDatabaseManager:
        """Crear gestor de base de datos"""
        return MongoDBIndexManager(connection)

class DatabaseService:
    """Servicio principal de base de datos (Facade Pattern)"""
    
    def __init__(self):
        self._connection: Optional[IDatabaseConnection] = None
        self._manager: Optional[IDatabaseManager] = None
    
    async def initialize(self) -> None:
        """Inicializar servicio de base de datos"""
        self._connection = DatabaseFactory.create_mongodb_connection()
        self._manager = DatabaseFactory.create_database_manager(self._connection)
        
        await self._connection.connect()
        await self._manager.create_collections()
        await self._manager.initialize_indexes()
    
    async def shutdown(self) -> None:
        """Cerrar servicio de base de datos"""
        if self._connection:
            await self._connection.disconnect()
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if not self._connection:
            raise RuntimeError("Servicio de base de datos no inicializado")
        return self._connection.get_database()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servicio"""
        if not self._connection:
            return {"status": "disconnected", "healthy": False}
        
        is_healthy = await self._connection.health_check()
        return {
            "status": "connected" if is_healthy else "error",
            "healthy": is_healthy,
            "database": settings.get_database_config().database_name
        }

# Singleton para el servicio de base de datos
class GlobalDatabaseService:
    """Singleton para servicio global de base de datos"""
    
    _instance = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_service(self) -> DatabaseService:
        """Obtener servicio de base de datos"""
        if self._service is None:
            self._service = DatabaseService()
        return self._service

# Instancia global
database_service = GlobalDatabaseService().get_service()

# Función de conveniencia para obtener base de datos
async def get_database() -> AsyncIOMotorDatabase:
    """Función helper para obtener base de datos (Dependency Injection)"""
    return database_service.get_database()