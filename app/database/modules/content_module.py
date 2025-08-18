# ===== app/database/modules/content_module.py =====
"""Módulo de contenidos educativos completo"""

from typing import Dict, Any
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class ContentModule(BaseModule):
    """Módulo completo de contenidos (Single Responsibility)"""
    
    def __init__(self, database):
        super().__init__(database)
        self._collections = [
            "contents",
            "content_categories",
            "file_uploads"
        ]
    
    async def _create_collections(self) -> None:
        """Crear colecciones de contenidos"""
        try:
            existing_collections = await self._database.list_collection_names()
            
            # Schema para contenidos
            content_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["title", "subject_id", "teacher_id", "content_type"],
                    "properties": {
                        "title": {"bsonType": "string", "minLength": 3, "maxLength": 200},
                        "description": {"bsonType": ["string", "null"], "maxLength": 2000},
                        "subject_id": {"bsonType": "objectId"},
                        "teacher_id": {"bsonType": "objectId"},
                        "content_type": {"enum": ["document", "video", "audio", "image", "link", "interactive"]},
                        "file_info": {"bsonType": ["object", "null"]},
                        "external_url": {"bsonType": ["string", "null"]},
                        "tags": {"bsonType": "array"},
                        "status": {"enum": ["draft", "published", "archived", "deleted"]}
                    }
                }
            }
            
            collections_config = {
                "contents": content_schema,
                "content_categories": {},
                "file_uploads": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await self._database.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección CONTENT '{collection_name}' creada con schema")
                    else:
                        await self._database.create_collection(collection_name)
                        logger.info(f"✅ Colección CONTENT '{collection_name}' creada")
        
        except Exception as e:
            logger.error(f"❌ Error creando colecciones CONTENT: {e}")
            raise e
    
    async def _create_indexes(self) -> None:
        """Crear índices de contenidos"""
        try:
            await self._database.contents.create_index("subject_id", name="idx_content_subject")
            await self._database.contents.create_index("teacher_id", name="idx_content_teacher")
            await self._database.contents.create_index("content_type", name="idx_content_type")
            await self._database.contents.create_index([("title", "text"), ("description", "text"), ("tags", "text")], name="idx_content_search")
            
            logger.info("✅ Índices CONTENT creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices CONTENT: {e}")
            raise e
    
    async def _get_module_collections(self) -> list:
        return self._collections
