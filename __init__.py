"""
BlenderCivil - Civil Engineering and Infrastructure Design Tools for Blender

This addon provides comprehensive tools for civil engineering workflows including:
- Horizontal and vertical alignment design
- Coordinate system management (OASYS integration)
- IFC/OpenBIM export (Bonsai/IfcOpenShell integration)
- Terrain modeling and analysis
- Infrastructure object libraries

Designed to integrate seamlessly with Bonsai (formerly BlenderBIM) and IfcOpenShell.
"""

bl_info = {
    "name": "BlenderCivil",
    "author": "Desert Springs Civil Engineering",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Civil",
    "description": "Civil engineering and infrastructure design tools",
    "warning": "Alpha version - expect changes",
    "doc_url": "https://github.com/DesertSpringsCivil/BlenderCivil",
    "tracker_url": "https://github.com/DesertSpringsCivil/BlenderCivil/issues",
    "category": "Scene",
}

import bpy
from bpy.utils import register_class, unregister_class

# Import modules
from . import preferences
from . import ui
from . import operators
from . import properties

# Check if Bonsai/IfcOpenShell is available
BONSAI_AVAILABLE = False
IFC_AVAILABLE = False

try:
    import ifcopenshell
    IFC_AVAILABLE = True
except ImportError:
    pass

try:
    from bonsai.bim.ifc import IfcStore
    BONSAI_AVAILABLE = True
except ImportError:
    pass

# Module list for registration
modules = (
    preferences,
    properties,
    operators,
    ui,
)

def register():
    """Register addon classes and properties"""
    
    # Register all classes from modules
    for module in modules:
        if hasattr(module, 'register'):
            module.register()
    
    # Print status
    print(f"\n{'='*60}")
    print(f"BlenderCivil v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]} loaded")
    print(f"{'='*60}")
    print(f"IfcOpenShell: {'✓ Available' if IFC_AVAILABLE else '✗ Not found'}")
    print(f"Bonsai: {'✓ Available' if BONSAI_AVAILABLE else '✗ Not found'}")
    print(f"{'='*60}\n")
    
    if not IFC_AVAILABLE:
        print("⚠️  Install IfcOpenShell for IFC export features")
    if not BONSAI_AVAILABLE:
        print("⚠️  Install Bonsai addon for OpenBIM integration")

def unregister():
    """Unregister addon classes and properties"""
    
    # Unregister in reverse order
    for module in reversed(modules):
        if hasattr(module, 'unregister'):
            module.unregister()
    
    print("BlenderCivil unloaded")

if __name__ == "__main__":
    register()
