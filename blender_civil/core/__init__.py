"""
BlenderCivil Core Modules
IFC management, alignment logic, and visualization
"""

from . import dependency_manager
from . import native_ifc_manager
from . import native_ifc_alignment
from . import alignment_visualizer

def register():
    """Register core modules"""
    # Core modules don't have classes to register
    pass

def unregister():
    """Unregister core modules"""
    pass
