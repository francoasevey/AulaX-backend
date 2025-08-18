# ===== app/database/modules/__init__.py =====
"""
Módulos de base de datos organizados por dominio

Cada módulo contiene:
- Schemas de validación
- Gestión de colecciones  
- Gestión de índices
- Lógica específica del dominio
"""

from .auth_module import AuthModule
from .academic_module import AcademicModule

__all__ = [
    "AuthModule",
    "AcademicModule"
]
