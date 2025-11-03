"""
BlenderCivil Operators Module

Blender operators for user actions and commands.
All operator classes will be organized here.
"""

import bpy
from .. import core

# Conditionally import operator modules based on IFC support
_operator_modules = []

if core.has_ifc_support():
    # Import core classes needed by operators
    from ..core.native_ifc_manager import NativeIfcManager
    from ..core.native_ifc_alignment import NativeIfcAlignment
    from ..core.alignment_visualizer import AlignmentVisualizer

    # Make them available to operator modules
    import sys
    current_module = sys.modules[__name__]
    current_module.NativeIfcManager = NativeIfcManager
    current_module.NativeIfcAlignment = NativeIfcAlignment
    current_module.AlignmentVisualizer = AlignmentVisualizer

    # Import operator modules
    from . import alignment_operators
    from . import file_operators
    from . import pi_operators
    from . import validation_operators
    from . import georef_operators
    from . import vertical_operators

    _operator_modules = [
        alignment_operators,
        file_operators,
        pi_operators,
        validation_operators,
        georef_operators,
        vertical_operators,
    ]


def register():
    """Register operators"""
    print("  [+] Operators module loaded")

    if _operator_modules:
        for module in _operator_modules:
            module.register()
        print(f"  [+] Registered {len(_operator_modules)} operator modules")
    else:
        print("  [!] IFC operators disabled (ifcopenshell not found)")


def unregister():
    """Unregister operators"""
    if _operator_modules:
        for module in reversed(_operator_modules):
            module.unregister()
