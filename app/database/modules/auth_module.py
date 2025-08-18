# ===== app/database/modules/auth_module.py - CORREGIDO FINAL =====
"""Módulo de autenticación con manejo robusto de índices"""

from typing import Dict, Any
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class AuthModule(BaseModule):
    """Módulo completo de autenticación (Single Responsibility)"""
    
    def __init__(self, database):
        super().__init__(database)
        self._collections = [
            "users",
            "user_sessions", 
            "parent_students",
            "password_resets",
            "email_verifications"
        ]
    
    async def _create_collections(self) -> None:
        """Crear colecciones de autenticación con schemas"""
        try:
            existing_collections = await self._database.list_collection_names()
            
            # Schema para usuarios (completo)
            user_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "password_hash", "role"],
                    "properties": {
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "password_hash": {"bsonType": "string", "minLength": 8},
                        "role": {"enum": ["administrator", "teacher", "student", "parent"]},
                        "status": {"enum": ["active", "inactive", "pending", "suspended"]},
                        "profile": {
                            "bsonType": "object",
                            "properties": {
                                "first_name": {"bsonType": "string", "maxLength": 50},
                                "last_name": {"bsonType": "string", "maxLength": 50},
                                "phone": {"bsonType": ["string", "null"]},
                                "avatar_url": {"bsonType": ["string", "null"]},
                                "bio": {"bsonType": ["string", "null"], "maxLength": 500}
                            }
                        },
                        "email_verified": {"bsonType": "bool"},
                        "is_active": {"bsonType": "bool"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"}
                    }
                }
            }
            
            # Schemas para otras colecciones
            session_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "token_hash", "expires_at"],
                    "properties": {
                        "user_id": {"bsonType": "objectId"},
                        "token_hash": {"bsonType": "string"},
                        "expires_at": {"bsonType": "date"},
                        "is_active": {"bsonType": "bool"},
                        "created_at": {"bsonType": "date"}
                    }
                }
            }
            
            # Colecciones con sus schemas
            collections_config = {
                "users": user_schema,
                "user_sessions": session_schema,
                "parent_students": {},
                "password_resets": {},
                "email_verifications": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await self._database.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección AUTH '{collection_name}' creada con schema")
                    else:
                        await self._database.create_collection(collection_name)
                        logger.info(f"✅ Colección AUTH '{collection_name}' creada")
        
        except Exception as e:
            logger.error(f"❌ Error creando colecciones AUTH: {e}")
            raise e
    
    async def _create_indexes(self) -> None:
        """Crear índices para el módulo AUTH con verificación robusta"""
        try:
            logger.info("📊 Creando índices AUTH...")
            
            # ===== ÍNDICES PARA COLECCIÓN USERS =====
            
            # Índice único para email
            await self._safe_create_index(
                "users",
                [("email", 1)],
                index_name="idx_user_email",
                unique=True
            )
            
            # Índice compuesto para role y status
            await self._safe_create_index(
                "users", 
                [("role", 1), ("status", 1)],
                index_name="idx_user_role_status"
            )
            
            # Índice para verificación y estado activo
            await self._safe_create_index(
                "users",
                [("email_verified", 1), ("is_active", 1)],
                index_name="idx_user_verification_active"
            )
            
            # Índice de texto para búsqueda
            await self._safe_create_index(
                "users",
                [("profile.first_name", "text"), ("profile.last_name", "text"), ("email", "text")], 
                index_name="idx_user_search"
            )
            
            # Índice para created_at (ordenamiento temporal)
            await self._safe_create_index(
                "users",
                [("created_at", -1)],
                index_name="idx_user_created_at"
            )
            
            # ===== ÍNDICES PARA COLECCIÓN USER_SESSIONS =====
            
            # Índice para user_id
            await self._safe_create_index(
                "user_sessions",
                [("user_id", 1)],
                index_name="idx_session_user"
            )
            
            # Índice único para token_hash
            await self._safe_create_index(
                "user_sessions",
                [("token_hash", 1)],
                index_name="idx_session_token",
                unique=True
            )
            
            # TTL index para expiración automática
            await self._safe_create_index(
                "user_sessions",
                [("expires_at", 1)],
                index_name="ttl_session_expiry",
                expireAfterSeconds=0
            )
            
            # Índice compuesto para sesiones activas
            await self._safe_create_index(
                "user_sessions",
                [("is_active", 1), ("expires_at", 1)],
                index_name="idx_session_active_expires"
            )
            
            # ===== ÍNDICES PARA COLECCIÓN PASSWORD_RESETS =====
            
            # Índice para email
            await self._safe_create_index(
                "password_resets",
                [("email", 1)],
                index_name="idx_reset_email"
            )
            
            # Índice único para token_hash
            await self._safe_create_index(
                "password_resets",
                [("token_hash", 1)],
                index_name="idx_reset_token",
                unique=True
            )
            
            # TTL index para expiración
            await self._safe_create_index(
                "password_resets",
                [("expires_at", 1)],
                index_name="ttl_reset_expiry",
                expireAfterSeconds=0
            )
            
            # Índice compuesto para resets no usados
            await self._safe_create_index(
                "password_resets",
                [("used", 1), ("expires_at", 1)],
                index_name="idx_reset_used_expires"
            )
            
            # ===== ÍNDICES PARA COLECCIÓN EMAIL_VERIFICATIONS =====
            
            # Índice para email
            await self._safe_create_index(
                "email_verifications",
                [("email", 1)],
                index_name="idx_verification_email"
            )
            
            # Índice único para token_hash
            await self._safe_create_index(
                "email_verifications",
                [("token_hash", 1)],
                index_name="idx_verification_token",
                unique=True
            )
            
            # TTL index para expiración
            await self._safe_create_index(
                "email_verifications",
                [("expires_at", 1)],
                index_name="ttl_verification_expiry",
                expireAfterSeconds=0
            )
            
            # Índice compuesto para verificaciones pendientes
            await self._safe_create_index(
                "email_verifications",
                [("verified", 1), ("expires_at", 1)],
                index_name="idx_verification_status_expires"
            )
            
            # ===== ÍNDICES PARA COLECCIÓN PARENT_STUDENTS =====
            
            # Índice para parent_id
            await self._safe_create_index(
                "parent_students",
                [("parent_id", 1)],
                index_name="idx_parent_students_parent"
            )
            
            # Índice para student_id
            await self._safe_create_index(
                "parent_students",
                [("student_id", 1)],
                index_name="idx_parent_students_student"
            )
            
            # Índice único compuesto para evitar duplicados
            await self._safe_create_index(
                "parent_students",
                [("parent_id", 1), ("student_id", 1)],
                index_name="idx_parent_students_unique",
                unique=True
            )
            
            logger.info("✅ Todos los índices AUTH creados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices AUTH: {e}")
            # No hacer raise para que la aplicación pueda continuar
    
    async def _get_module_collections(self) -> list:
        """Obtener colecciones del módulo AUTH"""
        return self._collections
    
    async def get_auth_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas específicas del módulo AUTH"""
        try:
            stats = {}
            
            # Contar usuarios por rol
            pipeline = [
                {"$group": {"_id": "$role", "count": {"$sum": 1}}}
            ]
            users_by_role = await self._database.users.aggregate(pipeline).to_list(length=None)
            stats["users_by_role"] = {item["_id"]: item["count"] for item in users_by_role}
            
            # Contar sesiones activas
            active_sessions = await self._database.user_sessions.count_documents({
                "is_active": True,
                "expires_at": {"$gt": "$$NOW"}
            })
            stats["active_sessions"] = active_sessions
            
            # Contar verificaciones pendientes
            pending_verifications = await self._database.email_verifications.count_documents({
                "verified": False,
                "expires_at": {"$gt": "$$NOW"}
            })
            stats["pending_verifications"] = pending_verifications
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas AUTH: {e}")
            return {"error": str(e)}