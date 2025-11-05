"""
BlenderCivil Core Module

Core functionality and data structures for BlenderCivil.
This will contain IFC utilities, geometry helpers, and core algorithms.
"""

import bpy

# Always import dependency_manager (no ifcopenshell dependency)
from . import dependency_manager

# Conditionally import IFC-dependent modules
_ifc_modules_loaded = False
_ifc_modules = []

try:
    import ifcopenshell

    # Import IFC-dependent modules
    from . import native_ifc_manager
    from . import native_ifc_alignment
    from . import native_ifc_vertical_alignment
    from . import native_ifc_cross_section
    from . import alignment_3d
    from . import alignment_visualizer
    from . import corridor_mesh_generator

    _ifc_modules = [
        native_ifc_manager,
        native_ifc_alignment,
        native_ifc_vertical_alignment,
        native_ifc_cross_section,
        alignment_3d,
        alignment_visualizer,
        corridor_mesh_generator,
    ]
    _ifc_modules_loaded = True

except ImportError as e:
    print(f"  [!] IFC modules not available: {e}")
    print(f"  [i] Install ifcopenshell to enable IFC features")


def register():
    """Register core module"""
    print("  [+] Core module loaded")

    if _ifc_modules_loaded:
        print("  [+] IFC features enabled")
    else:
        print("  [!] IFC features disabled (ifcopenshell not found)")


def unregister():
    """Unregister core module"""
    pass


def has_ifc_support():
    """Check if IFC support is available"""
    return _ifc_modules_loaded
