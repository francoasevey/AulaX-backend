
# ===== app/database/modules/base_module.py - CORREGIDO FINAL =====
"""Clase base para módulos de base de datos con manejo robusto de índices"""

from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseModule(ABC):
    """Clase base para módulos de base de datos (Template Method Pattern)"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._database = database
        self._name = self.__class__.__name__.replace("Module", "").lower()
    
    async def setup(self) -> None:
        """Template method para configuración de módulo"""
        logger.info(f"📦 Configurando módulo {self._name.upper()}...")
        
        # 1. Crear colecciones con schemas
        await self._create_collections()
        
        # 2. Crear índices
        await self._create_indexes()
        
        # 3. Configuración específica del módulo
        await self._setup_specific()
        
        logger.info(f"✅ Módulo {self._name.upper()} configurado")
    
    async def _safe_create_index(self, collection_name: str, index_spec, index_name: str = None, **kwargs):
        """
        Crear índice de forma segura con manejo robusto de conflictos
        """
        # Validación de index_name
        if index_name is None:
            logger.error("❌ index_name es requerido para crear índices")
            return
        
        try:
            collection = getattr(self._database, collection_name)
            
            # Obtener índices existentes
            existing_indexes = await collection.list_indexes().to_list(length=None)
            
            # Verificar si existe índice con el mismo nombre
            existing_index = None
            for idx in existing_indexes:
                if idx.get('name') == index_name:
                    existing_index = idx
                    break
            
            if existing_index:
                # Verificar si los campos son los mismos
                existing_key = existing_index.get('key', {})
                new_key = index_spec if isinstance(index_spec, dict) else dict(index_spec)
                
                if existing_key == new_key:
                    # Verificar opciones adicionales (unique, expireAfterSeconds, etc.)
                    existing_unique = existing_index.get('unique', False)
                    new_unique = kwargs.get('unique', False)
                    existing_ttl = existing_index.get('expireAfterSeconds')
                    new_ttl = kwargs.get('expireAfterSeconds')
                    
                    if existing_unique == new_unique and existing_ttl == new_ttl:
                        logger.info(f"✅ Índice '{index_name}' ya existe correctamente en '{collection_name}'")
                        return
                
                # Los campos o opciones son diferentes, eliminar el índice existente
                logger.warning(f"⚠️ Índice '{index_name}' existe con configuración diferente. Recreando...")
                logger.info(f"   Existente: {existing_key} (unique: {existing_index.get('unique', False)})")
                logger.info(f"   Nuevo: {new_key} (unique: {kwargs.get('unique', False)})")
                
                # No eliminar índices del sistema (_id_)
                if index_name != "_id_":
                    await collection.drop_index(index_name)
                    logger.info(f"✅ Índice '{index_name}' eliminado")
            
            # Crear el nuevo índice
            # Remover 'name' de kwargs si existe para evitar duplicados
            kwargs.pop('name', None)
            await collection.create_index(index_spec, name=index_name, **kwargs)
            logger.info(f"✅ Índice '{index_name}' creado en '{collection_name}'")
            
        except Exception as e:
            # Manejar errores específicos
            error_msg = str(e)
            if "IndexKeySpecsConflict" in error_msg:
                logger.warning(f"⚠️ Conflicto de índice '{index_name}' - omitiendo creación")
            elif "already exists" in error_msg.lower():
                logger.info(f"ℹ️ Índice '{index_name}' ya existe - omitiendo")
            else:
                logger.error(f"❌ Error creando índice '{index_name}' en '{collection_name}': {e}")
                # No hacer raise para que la aplicación pueda continuar
    
    @abstractmethod
    async def _create_collections(self) -> None:
        """Crear colecciones específicas del módulo"""
        pass
    
    @abstractmethod
    async def _create_indexes(self) -> None:
        """Crear índices específicos del módulo"""
        pass
    
    async def _setup_specific(self) -> None:
        """Configuración específica del módulo (opcional)"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del módulo"""
        try:
            collections = await self._get_module_collections()
            return {
                "status": "active",
                "collections": len(collections),
                "collection_names": collections
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    async def _get_module_collections(self) -> list:
        """Obtener colecciones del módulo"""
        all_collections = await self._database.list_collection_names()
        # Filtrar colecciones que pertenecen a este módulo
        # (implementación específica en cada módulo)
        return all_collections
    
    async def cleanup(self) -> None:
        """Limpieza al remover módulo (opcional)"""
        pass
