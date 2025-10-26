"""
BlenderCivil v0.3.0 - Professional Civil Engineering Tools for Blender
IFC-Compatible Alignment Design with Separate Entity Architecture

Main addon initialization file that registers all modules and components.

Author: BlenderCivil Development Team
Date: October 24, 2025
License: GPL v3
"""

bl_info = {
    "name": "BlenderCivil v0.3.0",
    "author": "BlenderCivil Development Team",
    "version": (0, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Civil Tab",
    "description": "Professional civil engineering tools with IFC-compatible alignment design",
    "warning": "Phase 1 - Separate Entity Architecture",
    "doc_url": "",
    "category": "Engineering",
}


import bpy

# Import all modules
from . import properties
from . import alignment_objects
from . import operators
from . import handlers
from . import ui


# List of modules to register (in order)
modules = (
    properties,
    operators,
    handlers,
    ui,
)


def register():
    """Register all addon components"""
    print("\n" + "="*60)
    print("BlenderCivil v0.3.0 - Professional Alignment System")
    print("Phase 1: Separate Entity Architecture")
    print("="*60)
    
    # Register all modules
    for module in modules:
        module.register()
    
    print("="*60)
    print("âœ“ BlenderCivil v0.3.0 ready!")
    print("  Access from: View3D > Sidebar (N) > Civil Tab")
    print("="*60 + "\n")


def unregister():
    """Unregister all addon components"""
    # Unregister in reverse order
    for module in reversed(modules):
        module.unregister()
    
    print("âœ“ BlenderCivil v0.3.0 unregistered")


if __name__ == "__main__":
    register()
