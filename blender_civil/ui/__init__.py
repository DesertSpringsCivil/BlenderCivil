"""
BlenderCivil UI Modules
Panels for dependency management, alignment, and validation
"""

from . import dependency_panel
from . import alignment_panel
from . import validation_panel

def register():
    """Register all UI panels"""
    dependency_panel.register()
    alignment_panel.register()
    validation_panel.register()

def unregister():
    """Unregister all UI panels"""
    validation_panel.unregister()
    alignment_panel.unregister()
    dependency_panel.unregister()
