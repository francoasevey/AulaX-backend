# app/config/database.py - Base de Datos Corregida
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
    """Implementación para MongoDB con flexibilidad de conexión"""
    
    def __init__(self, database_config: DatabaseConfiguration):
        self._config = database_config
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Conectar a MongoDB con configuración flexible"""
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
            logger.info(f"🔗 Host: {self._config.host}")
            logger.info(f"🔗 Puerto: {self._config.port}")
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
            logger.error(f"❌ Host: {self._config.host}")
            logger.error(f"❌ Puerto: {self._config.port}")
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

class MongoDBIndexManager(IDatabaseManager):
    """Gestor de índices para AULA X (Single Responsibility)"""
    
    def __init__(self, connection: IDatabaseConnection):
        self._connection = connection
    
    async def initialize_indexes(self) -> None:
        """Crear índices necesarios para AULA X"""
        try:
            db = self._connection.get_database()
            
            logger.info("📝 Creando índices de AULA X...")
            
            # === ÍNDICES PARA USUARIOS ===
            await db.users.create_index("email", unique=True, name="idx_user_email")
            await db.users.create_index([("role", 1), ("is_active", 1)], name="idx_user_role_status")
            await db.users.create_index([("role", 1), ("status", 1)], name="idx_user_role_active")
            
            # === ÍNDICES PARA MATERIAS ===
            await db.subjects.create_index("code", unique=True, name="idx_subject_code")
            await db.subjects.create_index("teacher_id", name="idx_subject_teacher")
            await db.subjects.create_index([("academic_year", 1), ("semester", 1)], name="idx_subject_period")
            await db.subjects.create_index("enrolled_students", name="idx_subject_students")
            
            # === ÍNDICES PARA TAREAS ===
            await db.tasks.create_index("subject_id", name="idx_task_subject")
            await db.tasks.create_index("teacher_id", name="idx_task_teacher")
            await db.tasks.create_index("due_date", name="idx_task_due_date")
            await db.tasks.create_index([("subject_id", 1), ("status", 1)], name="idx_task_subject_status")
            
            # === ÍNDICES PARA ENTREGAS DE TAREAS ===
            await db.task_submissions.create_index(
                [("task_id", 1), ("student_id", 1)], 
                unique=True, 
                name="idx_submission_unique"
            )
            await db.task_submissions.create_index("student_id", name="idx_submission_student")
            await db.task_submissions.create_index("submitted_at", name="idx_submission_date")
            await db.task_submissions.create_index("status", name="idx_submission_status")
            
            # === ÍNDICES PARA EVALUACIONES ===
            await db.task_evaluations.create_index("submission_id", unique=True, name="idx_evaluation_submission")
            await db.task_evaluations.create_index("student_id", name="idx_evaluation_student")
            await db.task_evaluations.create_index("status", name="idx_evaluation_status")
            
            # === ÍNDICES PARA CONTENIDOS ===
            await db.contents.create_index("subject_id", name="idx_content_subject")
            await db.contents.create_index("teacher_id", name="idx_content_teacher")
            await db.contents.create_index("content_type", name="idx_content_type")
            await db.contents.create_index([("subject_id", 1), ("status", 1)], name="idx_content_subject_status")
            
            # === ÍNDICES PARA PLANIFICACIÓN ===
            await db.class_plans.create_index("subject_id", name="idx_class_subject")
            await db.class_plans.create_index("teacher_id", name="idx_class_teacher")
            await db.class_plans.create_index("scheduled_date", name="idx_class_date")
            
            # === ÍNDICES PARA NOTIFICACIONES ===
            await db.notifications.create_index("recipient_id", name="idx_notification_recipient")
            await db.notifications.create_index([("recipient_id", 1), ("is_read", 1)], name="idx_notification_unread")
            await db.notifications.create_index("created_at", name="idx_notification_date")
            
            # Crear TTL para notificaciones expiradas
            await db.notifications.create_index(
                "expires_at",
                expireAfterSeconds=0,
                name="ttl_notification_expiry",
                partialFilterExpression={"expires_at": {"$exists": True}}
            )
            
            # === ÍNDICES PARA CHAT ===
            await db.chat_messages.create_index("subject_id", name="idx_chat_subject")
            await db.chat_messages.create_index([("subject_id", 1), ("created_at", 1)], name="idx_chat_timeline")
            await db.chat_messages.create_index("sender_id", name="idx_chat_sender")
            
            # === ÍNDICES PARA CALENDARIO ===
            await db.academic_calendar.create_index("start_date", name="idx_calendar_start")
            await db.academic_calendar.create_index([("subject_id", 1), ("start_date", 1)], name="idx_calendar_subject")
            
            # === ÍNDICES PARA RELACIONES PADRE-ESTUDIANTE ===
            await db.parent_students.create_index(
                [("parent_id", 1), ("student_id", 1)], 
                unique=True, 
                name="idx_parent_student_unique"
            )
            await db.parent_students.create_index("student_id", name="idx_parent_student")
            
            # === ÍNDICES DE BÚSQUEDA DE TEXTO ===
            await db.contents.create_index([
                ("title", "text"),
                ("description", "text"),
                ("tags", "text")
            ], name="idx_content_search")
            
            await db.subjects.create_index([
                ("name", "text"),
                ("description", "text"),
                ("code", "text")
            ], name="idx_subject_search")
            
            await db.users.create_index([
                ("profile.first_name", "text"),
                ("profile.last_name", "text"),
                ("email", "text")
            ], name="idx_user_search")
            
            logger.info("✅ Índices de AULA X creados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
            raise e
    
    async def create_collections(self) -> None:
        """Crear colecciones con validación de schema para AULA X"""
        try:
            db = self._connection.get_database()
            
            logger.info("📦 Creando colecciones de AULA X...")
            
            # Definir schemas de validación
            user_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "password_hash", "role"],
                    "properties": {
                        "email": {"bsonType": "string", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
                        "role": {"enum": ["administrator", "teacher", "student", "parent"]},
                        "status": {"enum": ["active", "inactive", "pending", "suspended"]},
                        "password_hash": {"bsonType": "string", "minLength": 8}
                    }
                }
            }
            
            subject_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "code", "teacher_id", "academic_year", "semester"],
                    "properties": {
                        "code": {"bsonType": "string", "pattern": "^[A-Z0-9\\-_]+$"},
                        "academic_year": {"bsonType": "int", "minimum": 2020, "maximum": 2030},
                        "semester": {"bsonType": "int", "minimum": 1, "maximum": 2},
                        "max_students": {"bsonType": "int", "minimum": 1, "maximum": 100}
                    }
                }
            }
            
            task_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["title", "subject_id", "teacher_id", "due_date"],
                    "properties": {
                        "status": {"enum": ["draft", "published", "closed", "archived"]},
                        "task_type": {"enum": ["assignment", "essay", "exam", "project", "quiz"]},
                        "max_points": {"bsonType": "number", "minimum": 0, "maximum": 100}
                    }
                }
            }
            
            # Crear colecciones con validación
            collections_config = {
                "users": user_schema,
                "subjects": subject_schema,
                "tasks": task_schema,
                "task_submissions": {},
                "task_evaluations": {},
                "contents": {},
                "class_plans": {},
                "notifications": {},
                "chat_messages": {},
                "academic_calendar": {},
                "parent_students": {},
                "content_categories": {}
            }
            
            existing_collections = await db.list_collection_names()
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await db.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección '{collection_name}' creada con validación")
                    else:
                        await db.create_collection(collection_name)
                        logger.info(f"✅ Colección '{collection_name}' creada")
                else:
                    logger.info(f"📦 Colección '{collection_name}' ya existe")
            
        except Exception as e:
            logger.error(f"❌ Error creando colecciones: {e}")
            raise e

class DatabaseFactory:
    """Factory para crear instancias de base de datos (Factory Pattern)"""
    
    @staticmethod
    def create_mongodb_connection() -> IDatabaseConnection:
        """Crear conexión MongoDB con configuración flexible"""
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
        logger.info("🚀 Inicializando servicio de base de datos...")
        
        self._connection = DatabaseFactory.create_mongodb_connection()
        self._manager = DatabaseFactory.create_database_manager(self._connection)
        
        await self._connection.connect()
        await self._manager.create_collections()
        await self._manager.initialize_indexes()
        
        # Crear datos iniciales si es necesario
        await self._create_initial_data()
        
        logger.info("🎉 Servicio de base de datos inicializado correctamente")
    
    async def _create_initial_data(self) -> None:
        """Crear datos iniciales si no existen"""
        try:
            db = self.get_database()
            
            # Verificar si ya existe un administrador
            admin_count = await db.users.count_documents({"role": "administrator"})
            
            if admin_count == 0:
                logger.info("👤 Creando usuario administrador inicial...")
                
                admin_user = {
                    "email": "admin@aulax.com",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPu8VDjL8QOrS",  # admin123
                    "role": "administrator",
                    "status": "active",
                    "profile": {
                        "first_name": "Administrador",
                        "last_name": "Sistema",
                        "phone": None,
                        "avatar_url": None,
                        "bio": "Usuario administrador del sistema"
                    },
                    "email_verified": True,
                    "created_at": {"$date": "2024-01-01T00:00:00.000Z"},
                    "updated_at": {"$date": "2024-01-01T00:00:00.000Z"},
                    "is_active": True
                }
                
                await db.users.insert_one(admin_user)
                logger.info("✅ Usuario administrador creado: admin@aulax.com / admin123")
        
        except Exception as e:
            logger.error(f"❌ Error creando datos iniciales: {e}")
    
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
        """Verificar salud del servicio con información detallada"""
        if not self._connection:
            return {
                "status": "disconnected", 
                "healthy": False,
                "connection_type": "none",
                "database": None
            }
        
        is_healthy = await self._connection.health_check()
        
        # Obtener estadísticas de la base de datos
        stats = {}
        try:
            if is_healthy:
                db = self.get_database()
                db_stats = await db.command("dbStats")
                collection_names = await db.list_collection_names()
                
                stats = {
                    "collections": len(collection_names),
                    "collection_names": collection_names,
                    "data_size": db_stats.get("dataSize", 0),
                    "storage_size": db_stats.get("storageSize", 0),
                    "indexes": db_stats.get("indexes", 0)
                }
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener estadísticas de BD: {e}")
        
        return {
            "status": "connected" if is_healthy else "error",
            "healthy": is_healthy,
            "connection_type": settings.get_connection_type(),
            "database": settings.get_database_config().database_name,
            "host": settings.MONGO_HOST,
            "port": settings.MONGO_PORT,
            "stats": stats
        }
    
    # Métodos para cambio dinámico de conexión
    async def switch_to_atlas(self, cluster_url: str, username: str, password: str, database: str = "aula_x") -> bool:
        """Cambiar a conexión Atlas"""
        try:
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb+srv://{username}:{password}@{cluster_url}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = MongoDBConnection(new_config)
            self._manager = DatabaseFactory.create_database_manager(self._connection)
            
            # Conectar y verificar
            await self._connection.connect()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a Atlas: {e}")
            return False
    
    async def switch_to_local(self, host: str = "localhost", port: int = 27017, database: str = "aula_x") -> bool:
        """Cambiar a conexión local"""
        try:
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb://{host}:{port}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = MongoDBConnection(new_config)
            self._manager = DatabaseFactory.create_database_manager(self._connection)
            
            # Conectar y verificar
            await self._connection.connect()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a local: {e}")
            return False
    
    async def switch_to_docker(self, host: str = "localhost", port: int = 27017, 
                             username: str = "admin", password: str = "admin123", 
                             database: str = "aula_x") -> bool:
        """Cambiar a conexión Docker"""
        try:
            # Cerrar conexión actual
            if self._connection:
                await self._connection.disconnect()
            
            # Actualizar configuración
            new_url = f"mongodb://{username}:{password}@{host}:{port}"
            new_config = DatabaseConfiguration(new_url, database)
            
            # Crear nueva conexión
            self._connection = MongoDBConnection(new_config)
            self._manager = DatabaseFactory.create_database_manager(self._connection)
            
            # Conectar y verificar
            await self._connection.connect()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando a Docker: {e}")
            return False

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
    
    def reset_service(self) -> DatabaseService:
        """Resetear servicio (útil para cambios de configuración)"""
        self._service = DatabaseService()
        return self._service

# Instancia global
database_service = GlobalDatabaseService().get_service()

# Función de conveniencia para obtener base de datos
async def get_database() -> AsyncIOMotorDatabase:
    """Función helper para obtener base de datos (Dependency Injection)"""
    return database_service.get_database()