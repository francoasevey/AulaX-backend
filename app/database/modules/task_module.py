# ===== app/database/modules/task_module.py =====
"""Módulo de tareas y evaluaciones completo"""

from typing import Dict, Any
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class TaskModule(BaseModule):
    """Módulo completo de tareas (Single Responsibility)"""
    
    def __init__(self, database):
        super().__init__(database)
        self._collections = [
            "tasks",
            "task_submissions",
            "task_evaluations",
            "ai_evaluations"
        ]
    
    async def _create_collections(self) -> None:
        """Crear colecciones de tareas con schemas"""
        try:
            existing_collections = await self._database.list_collection_names()
            
            # Schema para tareas
            task_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["title", "subject_id", "teacher_id", "due_date"],
                    "properties": {
                        "title": {"bsonType": "string", "minLength": 5, "maxLength": 200},
                        "description": {"bsonType": ["string", "null"], "maxLength": 5000},
                        "subject_id": {"bsonType": "objectId"},
                        "teacher_id": {"bsonType": "objectId"},
                        "task_type": {"enum": ["assignment", "essay", "exam", "project", "quiz"]},
                        "due_date": {"bsonType": "date"},
                        "max_points": {"bsonType": "number", "minimum": 0, "maximum": 100},
                        "ai_evaluation_enabled": {"bsonType": "bool"},
                        "status": {"enum": ["draft", "published", "closed", "archived"]}
                    }
                }
            }
            
            # Schema para entregas
            submission_schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["task_id", "student_id", "submitted_at"],
                    "properties": {
                        "task_id": {"bsonType": "objectId"},
                        "student_id": {"bsonType": "objectId"},
                        "submission_text": {"bsonType": ["string", "null"], "maxLength": 20000},
                        "files": {"bsonType": "array"},
                        "submitted_at": {"bsonType": "date"},
                        "is_late": {"bsonType": "bool"},
                        "status": {"enum": ["submitted", "processing", "evaluated", "returned"]}
                    }
                }
            }
            
            collections_config = {
                "tasks": task_schema,
                "task_submissions": submission_schema,
                "task_evaluations": {},
                "ai_evaluations": {}
            }
            
            for collection_name, schema in collections_config.items():
                if collection_name not in existing_collections:
                    if schema:
                        await self._database.create_collection(collection_name, validator=schema)
                        logger.info(f"✅ Colección TASK '{collection_name}' creada con schema")
                    else:
                        await self._database.create_collection(collection_name)
                        logger.info(f"✅ Colección TASK '{collection_name}' creada")
        
        except Exception as e:
            logger.error(f"❌ Error creando colecciones TASK: {e}")
            raise e
    
    async def _create_indexes(self) -> None:
        """Crear índices de tareas"""
        try:
            # Índices para tareas
            await self._database.tasks.create_index("subject_id", name="idx_task_subject")
            await self._database.tasks.create_index("teacher_id", name="idx_task_teacher")
            await self._database.tasks.create_index("due_date", name="idx_task_due_date")
            await self._database.tasks.create_index([("subject_id", 1), ("status", 1)], name="idx_task_subject_status")
            
            # Índices para entregas
            await self._database.task_submissions.create_index(
                [("task_id", 1), ("student_id", 1)], unique=True, name="idx_submission_unique"
            )
            await self._database.task_submissions.create_index("student_id", name="idx_submission_student")
            await self._database.task_submissions.create_index("submitted_at", name="idx_submission_date")
            
            # Índices para evaluaciones
            await self._database.task_evaluations.create_index("submission_id", unique=True, name="idx_evaluation_submission")
            await self._database.task_evaluations.create_index("student_id", name="idx_evaluation_student")
            
            logger.info("✅ Índices TASK creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices TASK: {e}")
            raise e
    
    async def _get_module_collections(self) -> list:
        return self._collections
