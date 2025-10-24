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
import sys
import importlib

# Check if we're reloading (for development)
if "properties" in locals():
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
    importlib.reload(preferences)
    print("BlenderCivil: Reloaded modules")
else:
    from . import properties
    from . import operators
    from . import ui
    from . import preferences
    print("BlenderCivil: Loaded modules")

# Check for optional dependencies
BONSAI_AVAILABLE = False
IFC_AVAILABLE = False

try:
    import ifcopenshell
    IFC_AVAILABLE = True
    print("BlenderCivil: IfcOpenShell available")
except ImportError:
    print("BlenderCivil: IfcOpenShell not available (optional)")

try:
    import bonsai
    BONSAI_AVAILABLE = True
    print("BlenderCivil: Bonsai available")
except ImportError:
    print("BlenderCivil: Bonsai not available (optional)")

# Module list for registration
modules = (
    properties,
    operators,
    ui,
    preferences,
)


def register():
    """Register addon classes and properties"""
    
    print(f"\n{'='*60}")
    print(f"Registering BlenderCivil v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
    print(f"{'='*60}")
    
    # Register all modules
    for module in modules:
        if hasattr(module, 'register'):
            try:
                module.register()
                print(f"✓ Registered: {module.__name__}")
            except Exception as e:
                print(f"✗ Error registering {module.__name__}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠ No register() in {module.__name__}")
    
    # Print status
    print(f"\n{'='*60}")
    print(f"BlenderCivil Loaded Successfully")
    print(f"{'='*60}")
    print(f"IfcOpenShell: {'✓ Available' if IFC_AVAILABLE else '✗ Not found (optional)'}")
    print(f"Bonsai: {'✓ Available' if BONSAI_AVAILABLE else '✗ Not found (optional)'}")
    print(f"{'='*60}")
    
    if not IFC_AVAILABLE:
        print("ℹ Install IfcOpenShell for IFC export features")
        print("  pip install ifcopenshell")
    if not BONSAI_AVAILABLE:
        print("ℹ Install Bonsai addon for full OpenBIM integration")
        print("  https://blenderbim.org/")
    
    print(f"{'='*60}\n")
    
    print("✓ Look for the 'Civil' tab in the 3D View sidebar (press N)")


def unregister():
    """Unregister addon classes and properties"""
    
    print("Unregistering BlenderCivil...")
    
    # Unregister in reverse order
    for module in reversed(modules):
        if hasattr(module, 'unregister'):
            try:
                module.unregister()
                print(f"✓ Unregistered: {module.__name__}")
            except Exception as e:
                print(f"✗ Error unregistering {module.__name__}: {e}")
    
    print("BlenderCivil unloaded")


if __name__ == "__main__":
    register()
