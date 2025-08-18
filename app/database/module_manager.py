# ===== app/database/module_manager.py =====
"""Gestor centralizado de módulos de base de datos"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List
import logging

from .modules.auth_module import AuthModule
from .modules.academic_module import AcademicModule
# from .modules.task_module import TaskModule        # ← Agregar después
# from .modules.content_module import ContentModule  # ← Agregar después
from .modules.auth_module import AuthModule
from .modules.academic_module import AcademicModule
from .modules.task_module import TaskModule
from .modules.content_module import ContentModule
from .modules.communication_module import CommunicationModule



logger = logging.getLogger(__name__)

class ModuleManager:
    """Gestor centralizado de módulos (Facade + Registry Pattern)"""
    
    def __init__(self, database: AsyncIOMotorDatabase, active_modules: List[str]):
        self._database = database
        self._active_modules = active_modules
        self._modules: Dict[str, Any] = {}
        
        # Registry de módulos disponibles
        self._available_modules = {
            "auth": AuthModule,
            #"academic": AcademicModule,
            # "tasks": TaskModule,        # ← Disponible cuando se cree
            # "content": ContentModule,   # ← Disponible cuando se cree
            # "communication": CommunicationModule,
            # "gamification": GamificationModule,
            # "analytics": AnalyticsModule
        }
    
    async def setup_modules(self) -> None:
        """Configurar todos los módulos activos"""
        logger.info("📦 Configurando módulos activos...")
        
        for module_name in self._active_modules:
            await self._setup_module(module_name)
        
        logger.info(f"✅ {len(self._modules)} módulos configurados exitosamente")
    
    async def _setup_module(self, module_name: str) -> None:
        """Configurar un módulo específico"""
        try:
            if module_name not in self._available_modules:
                logger.error(f"❌ Módulo '{module_name}' no disponible")
                return
            
            # Crear instancia del módulo
            module_class = self._available_modules[module_name]
            module_instance = module_class(self._database)
            
            # Configurar módulo
            await module_instance.setup()
            
            # Registrar módulo
            self._modules[module_name] = module_instance
            
            logger.info(f"✅ Módulo '{module_name}' configurado")
            
        except Exception as e:
            logger.error(f"❌ Error configurando módulo '{module_name}': {e}")
            raise e
    
    async def add_module(self, module_name: str) -> bool:
        """Agregar módulo dinámicamente"""
        try:
            if module_name not in self._modules:
                await self._setup_module(module_name)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error agregando módulo '{module_name}': {e}")
            return False
    
    async def remove_module(self, module_name: str) -> bool:
        """Remover módulo (no elimina datos)"""
        try:
            if module_name in self._modules:
                # Cleanup del módulo si es necesario
                if hasattr(self._modules[module_name], 'cleanup'):
                    await self._modules[module_name].cleanup()
                
                del self._modules[module_name]
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error removiendo módulo '{module_name}': {e}")
            return False
    
    def get_module(self, module_name: str):
        """Obtener instancia de un módulo"""
        return self._modules.get(module_name)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los módulos"""
        status = {
            "active_modules": len(self._modules),
            "available_modules": len(self._available_modules),
            "modules": {}
        }
        
        for module_name, module_instance in self._modules.items():
            try:
                if hasattr(module_instance, 'get_status'):
                    module_status = await module_instance.get_status()
                else:
                    module_status = {"status": "active"}
                
                status["modules"][module_name] = module_status
            except Exception as e:
                status["modules"][module_name] = {"status": "error", "error": str(e)}
        
        return status
