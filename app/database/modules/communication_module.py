# ===== app/database/modules/communication_module.py =====
"""Módulo de comunicación completo"""


from typing import Dict, Any
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class CommunicationModule(BaseModule):
    """Módulo completo de comunicación (Single Responsibility)"""
    
    def __init__(self, database):
        super().__init__(database)
        self._collections = [
            "notifications",
            "chat_messages",
            "aulabot_conversations"
        ]
    
    async def _create_collections(self) -> None:
        """Crear colecciones de comunicación"""
        try:
            existing_collections = await self._database.list_collection_names()
            
            # Schema para notificaciones
            notification_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["recipient_id", "title", "message", "type"],
                    "properties": {
                        "recipient_id": {"bsonType": "objectId"},
                        "sender_id": {"bsonType": ["objectId", "null"]},
                        "title": {"bsonType": "string", "minLength": 1, "maxLength": 200},
                        "message": {"bsonType": "string", "minLength": 1, "maxLength": 2000},
                        "type": {"enum": ["info", "warning", "success", "error", "task", "grade", "reminder"]},
                        "priority": {"enum": ["low", "medium", "high", "urgent"]},
                        "is_read": {"bsonType": "bool"},
                        "created_at": {"bsonType": "date"}
                    }
                }
            }
            
            # Schema para chat
            chat_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["subject_id", "sender_id", "message"],
                    "properties": {
                        "subject_id": {"bsonType": "objectId"},
                        "sender_id": {"bsonType": "objectId"},
                        "message": {"bsonType": "string", "minLength": 1, "maxLength": 5000},
                        "message_type": {"enum": ["text", "file", "image", "system"]},
                        "file_attachments": {"bsonType": "array"},
                        "created_at": {"bsonType": "date"}
                    }
                }
            }
            
            collections_config = {
                "notifications": notification_schema,
                "chat_messages": chat_schema,
                "aulabot_conversations": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await self._database.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección COMM '{collection_name}' creada con schema")
                    else:
                        await self._database.create_collection(collection_name)
                        logger.info(f"✅ Colección COMM '{collection_name}' creada")
        
        except Exception as e:
            logger.error(f"❌ Error creando colecciones COMM: {e}")
            raise e
    
    async def _create_indexes(self) -> None:
        """Crear índices de comunicación"""
        try:
            # Índices para notificaciones
            await self._database.notifications.create_index("recipient_id", name="idx_notification_recipient")
            await self._database.notifications.create_index([("recipient_id", 1), ("is_read", 1)], name="idx_notification_unread")
            await self._database.notifications.create_index("created_at", name="idx_notification_date")
            
            # TTL para notificaciones expiradas
            await self._database.notifications.create_index(
                "expires_at", expireAfterSeconds=0, name="ttl_notification_expiry",
                partialFilterExpression={"expires_at": {"$exists": True}}
            )
            
            # Índices para chat
            await self._database.chat_messages.create_index("subject_id", name="idx_chat_subject")
            await self._database.chat_messages.create_index([("subject_id", 1), ("created_at", 1)], name="idx_chat_timeline")
            await self._database.chat_messages.create_index("sender_id", name="idx_chat_sender")
            
            logger.info("✅ Índices COMM creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices COMM: {e}")
            raise e
    
    async def _get_module_collections(self) -> list:
        return self._collections
