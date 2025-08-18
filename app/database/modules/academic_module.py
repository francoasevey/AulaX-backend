# ===== app/database/modules/academic_module.py =====
"""Módulo académico completo"""

from typing import Dict, Any  
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class AcademicModule(BaseModule):
    """Módulo completo académico (Single Responsibility)"""
    
    def __init__(self, database):
        super().__init__(database)
        self._collections = [
            "subjects",
            "class_plans",
            "academic_calendar",
            "enrollments"
        ]
    
    async def _create_collections(self) -> None:
        """Crear colecciones académicas"""
        try:
            existing_collections = await self._database.list_collection_names()
            
            # Schema para materias
            subject_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "code", "teacher_id", "academic_year", "semester"],
                    "properties": {
                        "name": {"bsonType": "string", "maxLength": 100},
                        "code": {"bsonType": "string", "pattern": "^[A-Z0-9\\-_]+$"},
                        "teacher_id": {"bsonType": "objectId"},
                        "academic_year": {"bsonType": "int", "minimum": 2020, "maximum": 2030},
                        "semester": {"bsonType": "int", "minimum": 1, "maximum": 2},
                        "status": {"enum": ["active", "inactive", "completed", "cancelled"]}
                    }
                }
            }
            
            collections_config = {
                "subjects": subject_schema,
                "class_plans": {},
                "academic_calendar": {},
                "enrollments": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await self._database.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección ACADEMIC '{collection_name}' creada con schema")
                    else:
                        await self._database.create_collection(collection_name)
                        logger.info(f"✅ Colección ACADEMIC '{collection_name}' creada")
        
        except Exception as e:
            logger.error(f"❌ Error creando colecciones ACADEMIC: {e}")
            raise e
    
    async def _create_indexes(self) -> None:
        """Crear índices académicos"""
        try:
            await self._database.subjects.create_index(
                "code", unique=True, name="idx_subject_code"
            )
            await self._database.subjects.create_index(
                "teacher_id", name="idx_subject_teacher"
            )
            await self._database.subjects.create_index(
                [("academic_year", 1), ("semester", 1)], name="idx_subject_period"
            )
            
            logger.info("✅ Índices ACADEMIC creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices ACADEMIC: {e}")
            raise e
    
    async def _get_module_collections(self) -> list:
        """Obtener colecciones del módulo ACADEMIC"""
        return self._collections
